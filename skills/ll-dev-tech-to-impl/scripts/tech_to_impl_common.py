skill_id: ll-dev-tech-to-impl
skill_type: workflow
version: 0.1.0
workflow_key: dev.tech-to-impl

authority:
  canonical_template: E:\ai\LEE\spec-global\departments\dev\workflows\templates\feature-delivery-l2-template.yaml
  governing_adrs:
    - E:\ai\LEE\spec\adr\ADR-008__dev-department-ssot-alignment-and-workflow-reframe.md
    - E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-013-FEAT-to-TECH Lite-Native Skill 设计派生冻结基线.MD
    - E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-014-TECH-to-IMPL Lite-Native Skill 实施候选冻结基线.MD
  upstream_skill: ll-dev-feat-to-tech
  upstream_plan_template: E:\ai\LEE\spec-global\departments\product\workflows\templates\feat-to-delivery-prep\v1\workflow.yaml
  downstream_template_id: template.dev.feature_delivery_l2

roles:
  executor:
    required: true
    evidence_required: true
    prompt_file: agents/executor.md
  supervisor:
    required: true
    evidence_required: true
    prompt_file: agents/supervisor.md

runtime:
  mode: lite_native
  command: python scripts/tech_to_impl.py run --input <tech-package-dir> --feat-ref <feat-ref> --tech-ref <tech-ref> --repo-root <repo-root>
  entry_script: scripts/tech_to_impl.py
  accepted_input_paths:
    - artifacts/feat-to-tech/<run_id>
    - direct tech_design_package directory path
  produced_output_dir: artifacts/tech-to-impl/<run_id>--<tech_ref>
  required_output_artifacts:
    - package-manifest.json
    - impl-bundle.md
    - impl-bundle.json
    - impl-task.md
    - upstream-design-refs.json
    - integration-plan.md
    - dev-evidence-plan.json
    - smoke-gate-subject.json
    - impl-review-report.json
    - impl-acceptance-report.json
    - impl-defect-list.json
    - handoff-to-feature-delivery.json
    - execution-evidence.json
    - supervision-evidence.json

input:
  artifact_type: tech_design_package
  contract_file: input/contract.yaml
  schema_file: input/schema.json
  structural_validation_required: true
  semantic_validation_required: true

output:
  artifact_type: feature_impl_candidate_package
  contract_file: output/contract.yaml
  schema_file: output/schema.json
  template_file: output/template.md
  structural_validation_required: true
  semantic_validation_required: true

validation:
  structural:
    - "python scripts/tech_to_impl.py validate-input --input $INPUT --feat-ref $FEAT_REF --tech-ref $TECH_REF"
    - "python scripts/tech_to_impl.py run --input $INPUT --feat-ref $FEAT_REF --tech-ref $TECH_REF --repo-root $REPO_ROOT --allow-update"
    - "python scripts/tech_to_impl.py validate-output --artifacts-dir $OUTPUT"
    - "python scripts/tech_to_impl.py validate-package-readiness --artifacts-dir $OUTPUT"
    - "python scripts/tech_to_impl.py freeze-guard --artifacts-dir $OUTPUT"
  semantic:
    input_checklist: input/semantic-checklist.md
    output_checklist: output/semantic-checklist.md

evidence:
  execution_schema: evidence/execution-evidence.schema.json
  supervision_schema: evidence/supervision-evidence.schema.json
  report_template: evidence/report.template.md

lifecycle:
  definition_file: ll.lifecycle.yaml
  max_revision_rounds: 3

gate:
  freeze_requires:
    - input_structural_pass
    - input_semantic_pass
    - output_structural_pass
    - output_semantic_pass
    - execution_evidence_present
    - supervision_evidence_present
    - execution_handoff_present
  reject_when:
    - upstream_package_not_freeze_ready
    - selected_feat_ref_missing
    - selected_tech_ref_missing
    - missing_upstream_design_refs
    - no_execution_surface_selected
    - impl_rewrites_upstream_design
    - status_model_inconsistent
    - required_evidence_missing

version: 0.1.0
states:
  - drafted
  - structurally_validated
  - semantically_reviewed
  - revised
  - accepted
  - frozen
  - rejected

transitions:
  drafted:
    - structurally_validated
    - rejected
  structurally_validated:
    - semantically_reviewed
    - revised
    - rejected
  semantically_reviewed:
    - accepted
    - revised
    - rejected
  revised:
    - structurally_validated
    - rejected
  accepted:
    - frozen
    - revised
  frozen: []
  rejected: []

limits:
  max_revision_rounds: 3

---
name: ll-dev-tech-to-impl
description: Governed LL workflow skill for transforming one frozen TECH package plus selected feat_ref and tech_ref into a task-first implementation candidate package aligned to ADR-008 and ADR-014.
---

# LL Dev TECH to IMPL

This skill freezes the task-first `feat2impl` boundary. It does not claim code is finished. It derives one governed `feature_impl_candidate_package` that packages the implementation task entry for the canonical Dev Feature Delivery L2 chain.

## Canonical Authority

- Department ADR: `E:\ai\LEE\spec\adr\ADR-008__dev-department-ssot-alignment-and-workflow-reframe.md`
- Local ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-014-TECH-to-IMPL Lite-Native Skill 实施候选冻结基线.MD`
- Dev template authority: `E:\ai\LEE\spec-global\departments\dev\workflows\templates\feature-delivery-l2-template.yaml`
- Upstream governed skill: `ll-dev-feat-to-tech`
- Upstream planning context: `E:\ai\LEE\spec-global\departments\product\workflows\templates\feat-to-delivery-prep\v1\workflow.yaml`
- Downstream target template: `template.dev.feature_delivery_l2`
- Primary runtime command: `python scripts/tech_to_impl.py run --input <tech-package-dir> --feat-ref <feat-ref> --tech-ref <tech-ref> --repo-root <repo-root>`

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `resources/upstream-workflow-analysis.md`
5. `agents/executor.md`
6. `agents/supervisor.md`
7. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Execution Protocol

1. Accept only a freeze-ready `tech_design_package` emitted by `ll-dev-feat-to-tech`, plus explicit `feat_ref` and `tech_ref`.
2. Validate the package structurally before drafting any implementation candidate output.
3. Resolve the authoritative selected FEAT and its frozen `TECH / ARCH / API` references from the upstream TECH package.
4. Run `python scripts/tech_to_impl.py executor-run --input <tech-package-dir> --feat-ref <feat-ref> --tech-ref <tech-ref>` to generate the governed implementation task package.
5. Always produce `impl-task.md`, `upstream-design-refs.json`, `integration-plan.md`, `dev-evidence-plan.json`, and `smoke-gate-subject.json`.
6. Emit frontend, backend, and migration workstreams only when the applicability assessment justifies them.
7. Record execution evidence, then hand the package to the supervisor.
8. Run `python scripts/tech_to_impl.py supervisor-review --artifacts-dir <impl-package-dir>` before marking the package execution-ready.
9. Freeze only after the supervisor records a semantic pass and `python scripts/tech_to_impl.py freeze-guard --artifacts-dir <impl-package-dir>` returns success.
10. Emit a handoff that preserves `feat_ref`, `impl_ref`, `tech_ref`, and optional `arch_ref / api_ref`, with the canonical `template.dev.feature_delivery_l2` target.

## Workflow Boundary

- Input: one freeze-ready `tech_design_package` plus one selected `feat_ref` and one selected `tech_ref`
- Output: one `feature_impl_candidate_package`
- Mandatory package contents: `impl-task.md`, `upstream-design-refs.json`, `integration-plan.md`, `dev-evidence-plan.json`, `smoke-gate-subject.json`
- Optional package contents: `frontend-workstream.md`, `backend-workstream.md`, `migration-cutover-plan.md`
- Out of scope: redefining technical design, inventing new product scope, claiming final code delivery completed, or bypassing the downstream Feature Delivery L2 chain

## Non-Negotiable Rules

- Do not accept raw requirements, FEAT markdown, or unfrozen TECH notes outside a governed `tech_design_package`.
- Do not let IMPL become a second technical design document; TECH remains the design truth source.
- Do not emit frontend, backend, or migration workstreams mechanically; applicability must be explicit.
- Do not allow a package with no frontend or backend execution surface to pass readiness.
- Do not let the executor self-approve semantic validity or mark execution-ready without supervisor evidence.

# Executor

You are the executor for `ll-dev-tech-to-impl`.

## Responsibilities

1. Resolve one authoritative `TECH` package together with the selected `feat_ref` and `tech_ref`.
2. Derive a task-first implementation candidate package aligned to ADR-008, ADR-014, and `template.dev.feature_delivery_l2`.
3. Always emit `impl-task.md`, `upstream-design-refs.json`, `integration-plan.md`, `dev-evidence-plan.json`, and `smoke-gate-subject.json`.
4. Emit frontend, backend, and migration workstreams only when the applicability assessment justifies them.
5. Record execution evidence for all significant commands, decisions, and uncertainties.
6. Hand the result to the supervisor after structural validation passes.

## Forbidden Actions

- issuing the final semantic pass
- claiming final implementation or smoke-gate success
- rewriting upstream `TECH / ARCH / API` decisions inside IMPL
- adding product scope not justified by the selected TECH package

interface:
  display_name: "LL Dev Tech To Impl"
  short_description: "Governed skill for LL Dev Tech To Impl"
  default_prompt: "Use $ll-dev-tech-to-impl to run the governed ll-dev-tech-to-impl workflow."

# Supervisor

You are the supervisor for `ll-dev-tech-to-impl`.

## Responsibilities

1. Review the generated implementation task package, the selected TECH authority, and the execution evidence.
2. Check that the package remains at the Dev implementation-entry layer and does not drift into second-layer technical design, release planning, or final-delivery claims.
3. Verify that workstream applicability is explicit and that mandatory IMPL artifacts stay present.
4. Decide `pass`, `revise`, or `reject`.
5. Record supervision evidence with concrete findings and a reasoned decision.
6. Mark the package execution-ready only when the handoff to `template.dev.feature_delivery_l2` is structurally and semantically coherent.

## Forbidden Actions

- silent approval without evidence
- rewriting the artifact without recording a review decision
- approving a package with no frontend or backend execution surface selected
- overriding lineage or upstream design reference failures

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ll-dev-tech-to-impl execution evidence",
  "type": "object",
  "required": [
    "skill_id",
    "run_id",
    "role",
    "inputs",
    "outputs",
    "commands_run",
    "structural_results",
    "key_decisions",
    "uncertainties"
  ],
  "properties": {
    "skill_id": {
      "type": "string"
    },
    "run_id": {
      "type": "string"
    },
    "role": {
      "type": "string",
      "const": "executor"
    },
    "inputs": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "outputs": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "commands_run": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "structural_results": {
      "type": "object"
    },
    "key_decisions": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "uncertainties": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "additionalProperties": true
}

# ll-dev-tech-to-impl Review Report

## Run Summary

- run_id:
- workflow:
- input_ref:
- output_ref:

## Structural Validation

- input:
- output:

## Execution Evidence

- commands:
- decisions:
- uncertainties:

## Supervision Evidence

- findings:
- decision:
- reason:

## Freeze Decision

- status:
- gate_results:

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ll-dev-tech-to-impl supervision evidence",
  "type": "object",
  "required": [
    "skill_id",
    "run_id",
    "role",
    "reviewed_inputs",
    "reviewed_outputs",
    "semantic_findings",
    "decision",
    "reason"
  ],
  "properties": {
    "skill_id": {
      "type": "string"
    },
    "run_id": {
      "type": "string"
    },
    "role": {
      "type": "string",
      "const": "supervisor"
    },
    "reviewed_inputs": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "reviewed_outputs": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "semantic_findings": {
      "type": "array",
      "items": {
        "type": "object"
      }
    },
    "decision": {
      "type": "string",
      "enum": [
        "pass",
        "revise",
        "reject"
      ]
    },
    "reason": {
      "type": "string"
    }
  },
  "additionalProperties": true
}

artifact_type: tech_design_package
schema_version: 1.0.0
authoritative_upstream_skill: ll-dev-feat-to-tech
accepted_statuses:
  - accepted
  - frozen
required_runtime_artifacts:
  - package-manifest.json
  - tech-design-bundle.md
  - tech-design-bundle.json
  - tech-spec.md
  - tech-impl.md
  - tech-review-report.json
  - tech-acceptance-report.json
  - tech-defect-list.json
  - tech-freeze-gate.json
  - handoff-to-tech-impl.json
  - execution-evidence.json
  - supervision-evidence.json
required_fields:
  - artifact_type
  - workflow_key
  - workflow_run_id
  - status
  - schema_version
  - feat_ref
  - tech_ref
  - selected_feat
  - source_refs
required_selected_feat_fields:
  - feat_ref
  - title
  - goal
  - scope
  - constraints
required_selector_fields:
  - feat_ref
  - tech_ref
structural_checks:
  - required_artifact_presence
  - upstream_workflow_is_dev.feat-to-tech
  - tech_freeze_gate_is_pass
  - selected_feat_ref_present
  - selected_tech_ref_present
  - upstream_feat_lineage_present
  - evidence_presence
semantic_gate:
  required: true
forbidden_statuses:
  - revised
  - rejected
forbidden_inputs:
  - raw_requirement
  - feat_freeze_package
  - direct_task_list
  - shadow_tech_doc
notes:
  - The selected TECH package must already be independently acceptable at the TECH layer before implementation planning begins.
  - `feat_ref` and `tech_ref` selection are both mandatory because IMPL now derives from frozen TECH authority, not raw FEAT notes.
  - Upstream TECH lineage must preserve FEAT, EPIC, and SRC references, with optional ARCH/API refs when present.

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ll-dev-tech-to-impl input",
  "type": "object",
  "required": [
    "artifact_type",
    "workflow_key",
    "workflow_run_id",
    "status",
    "schema_version",
    "feat_ref",
    "tech_ref",
    "selected_feat",
    "source_refs"
  ],
  "properties": {
    "artifact_type": {
      "type": "string",
      "const": "tech_design_package"
    },
    "workflow_key": {
      "type": "string",
      "const": "dev.feat-to-tech"
    },
    "workflow_run_id": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "schema_version": {
      "type": "string"
    },
    "feat_ref": {
      "type": "string"
    },
    "tech_ref": {
      "type": "string"
    },
    "arch_ref": {
      "type": ["string", "null"]
    },
    "api_ref": {
      "type": ["string", "null"]
    },
    "selected_feat": {
      "type": "object",
      "required": ["feat_ref", "title", "goal", "scope", "constraints"],
      "properties": {
        "feat_ref": { "type": "string" },
        "title": { "type": "string" },
        "goal": { "type": "string" },
        "scope": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string" }
        },
        "constraints": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string" }
        },
        "dependencies": {
          "type": "array",
          "items": { "type": "string" }
        },
        "acceptance_checks": {
          "type": "array",
          "items": { "type": "object" }
        }
      },
      "additionalProperties": true
    },
    "source_refs": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    }
  },
  "additionalProperties": true
}

# Input Semantic Checklist

Review the selected TECH package for task-first implementation readiness.

- Is the package already freeze-ready at the TECH layer, not merely structurally present?
- Does the selected `tech_ref` remain the authoritative technical design source for the selected `feat_ref`?
- Are scope, constraints, dependencies, and acceptance checks explicit enough to derive implementation tasks without inventing new design truth?
- If `ARCH` or `API` are present, are they referenced as inherited authorities rather than restated or re-decided?
- Would accepting this TECH package force IMPL to guess boundaries that should have been fixed upstream?

artifact_type: feature_impl_candidate_package
schema_version: 1.0.0
required_runtime_artifacts:
  - package-manifest.json
  - impl-bundle.md
  - impl-bundle.json
  - impl-task.md
  - upstream-design-refs.json
  - integration-plan.md
  - dev-evidence-plan.json
  - smoke-gate-subject.json
  - impl-review-report.json
  - impl-acceptance-report.json
  - impl-defect-list.json
  - handoff-to-feature-delivery.json
  - execution-evidence.json
  - supervision-evidence.json
required_source_refs:
  - "dev.feat-to-tech::<run_id>"
  - "FEAT-*"
  - "TECH-*"
  - "EPIC-*"
  - "SRC-*"
required_output_objects:
  - IMPL_TASK
  - UPSTREAM_DESIGN_REFS
required_bundle_sections:
  - Selected Upstream
  - Applicability Assessment
  - Implementation Task
  - Integration Plan
  - Evidence Plan
  - Smoke Gate Subject
  - Delivery Handoff
  - Traceability
required_impl_task_sections:
  - 1. 目标
  - 2. 上游依赖
  - 3. 实施范围
  - 4. 实施步骤
  - 5. 风险与阻塞
  - 6. 交付物
  - 7. 验收检查点
conditional_output_objects:
  - FRONTEND_WORKSTREAM
  - BACKEND_WORKSTREAM
  - MIGRATION_CUTOVER_PLAN
structural_checks:
  - schema
  - trace
  - mandatory_artifact_presence
  - applicability_assessment_consistency
  - status_model_consistency
  - downstream_handoff_presence
semantic_gate:
  required: true
forbidden_content:
  - second_layer_technical_design
  - release_plan_truth
  - qa_strategy_truth
  - unstated_new_requirements
  - code_completion_claim_without_execution
notes:
  - `impl-task.md`, `upstream-design-refs.json`, `integration-plan.md`, `dev-evidence-plan.json`, and `smoke-gate-subject.json` are mandatory in every run.
  - Frontend, backend, and migration workstreams are conditional and must follow explicit applicability assessment.
  - The package is the execution-entry truth for `template.dev.feature_delivery_l2`, not final code-delivery proof.

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ll-dev-tech-to-impl output",
  "type": "object",
  "required": [
    "artifact_type",
    "workflow_key",
    "workflow_run_id",
    "status",
    "schema_version",
    "package_role",
    "feat_ref",
    "impl_ref",
    "tech_ref",
    "source_refs",
    "workstream_assessment",
    "artifact_refs"
  ],
  "properties": {
    "artifact_type": {
      "type": "string",
      "const": "feature_impl_candidate_package"
    },
    "workflow_key": {
      "type": "string",
      "const": "dev.tech-to-impl"
    },
    "workflow_run_id": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": ["in_progress", "execution_ready", "blocked"]
    },
    "schema_version": {
      "type": "string"
    },
    "package_role": {
      "type": "string",
      "const": "candidate"
    },
    "feat_ref": {
      "type": "string"
    },
    "impl_ref": {
      "type": "string"
    },
    "tech_ref": {
      "type": "string"
    },
    "arch_ref": {
      "type": ["string", "null"]
    },
    "api_ref": {
      "type": ["string", "null"]
    },
    "source_refs": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    },
    "workstream_assessment": {
      "type": "object",
      "required": ["frontend_required", "backend_required", "migration_required", "rationale"],
      "properties": {
        "frontend_required": { "type": "boolean" },
        "backend_required": { "type": "boolean" },
        "migration_required": { "type": "boolean" },
        "execution_surface_count": { "type": "integer" },
        "rationale": {
          "type": "object",
          "additionalProperties": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      },
      "additionalProperties": true
    },
    "artifact_refs": {
      "type": "object",
      "required": [
        "bundle_markdown",
        "bundle_json",
        "impl_task",
        "upstream_design_refs",
        "integration_plan",
        "dev_evidence_plan",
        "smoke_gate_subject",
        "review_report",
        "acceptance_report",
        "defect_list",
        "handoff"
      ],
      "properties": {
        "bundle_markdown": { "type": "string" },
        "bundle_json": { "type": "string" },
        "impl_task": { "type": "string" },
        "upstream_design_refs": { "type": "string" },
        "frontend_workstream": { "type": ["string", "null"] },
        "backend_workstream": { "type": ["string", "null"] },
        "migration_cutover_plan": { "type": ["string", "null"] },
        "integration_plan": { "type": "string" },
        "dev_evidence_plan": { "type": "string" },
        "smoke_gate_subject": { "type": "string" },
        "review_report": { "type": "string" },
        "acceptance_report": { "type": "string" },
        "defect_list": { "type": "string" },
        "handoff": { "type": "string" }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}

# Output Semantic Checklist

Review the `feature_impl_candidate_package` against the selected TECH package.

- Is `impl-task.md` clearly task-first rather than a rewritten technical design?
- Is `upstream-design-refs.json` explicit enough that downstream execution does not need to guess `TECH / ARCH / API` authority?
- Are frontend, backend, and migration workstreams emitted only when the applicability assessment justifies them?
- Does the package stay at the implementation-candidate layer instead of drifting into release planning, QA strategy, or code-complete claims?
- Does the handoff to `template.dev.feature_delivery_l2` preserve `feat_ref`, `impl_ref`, `tech_ref`, and optional `arch_ref / api_ref`?

---
artifact_type: feature_impl_candidate_package
workflow_key: dev.tech-to-impl
status: in_progress
package_role: candidate
schema_version: 1.0.0
source_refs:
  - dev.feat-to-tech::RUN-ID
feat_ref: FEAT-TODO
impl_ref: IMPL-FEAT-TODO
tech_ref: TECH-FEAT-TODO
---

# {{TITLE}}

## Selected Upstream

[Summarize the selected FEAT and inherited TECH authority.]

## Applicability Assessment

[State whether frontend, backend, and migration workstreams apply, and why.]

## Implementation Task

[Summarize the implementation task entry and point to `impl-task.md`.]

## Integration Plan

[Summarize integration sequencing assumptions.]

## Evidence Plan

[Summarize evidence coverage expectations for downstream execution.]

## Smoke Gate Subject

[Summarize the blocked/ready criteria for smoke review.]

## Delivery Handoff

[Describe the canonical handoff into `template.dev.feature_delivery_l2`.]

## Traceability

[Map output sections back to authoritative TECH and FEAT refs.]

# Glossary

- contract: explicit input or output requirements for an artifact.
- structural validation: deterministic checks such as schema, naming, refs, or file presence.
- semantic validation: review of fidelity, scope, and artifact responsibility.
- execution evidence: executor record of commands, decisions, and uncertainties.
- supervision evidence: supervisor record of findings and disposition.
- freeze gate: final condition set that must pass before an artifact is treated as governed truth.

# Upstream Workflow Analysis

This reference maps ADR-008, ADR-014, the canonical Dev Feature Delivery L2 template, and the product `feat-to-delivery-prep` workflow into a lite-native TECH to IMPL candidate workflow.

## Canonical Source

- Dev template path: `E:\ai\LEE\spec-global\departments\dev\workflows\templates\feature-delivery-l2-template.yaml`
- Dev template id: `template.dev.feature_delivery_l2`
- Governing ADRs:
  - `E:\ai\LEE\spec\adr\ADR-008__dev-department-ssot-alignment-and-workflow-reframe.md`
  - `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-014-TECH-to-IMPL Lite-Native Skill 实施候选冻结基线.MD`
- Upstream governed skill: `ll-dev-feat-to-tech`
- Upstream planning context: `E:\ai\LEE\spec-global\departments\product\workflows\templates\feat-to-delivery-prep\v1\workflow.yaml`

## Stage Mapping

The lite-native runtime does not directly execute code. It derives one implementation entry package that preserves the canonical L2 phase chain:

1. `implementation_task`
2. `frontend`
3. `backend`
4. `migration`
5. `integration`
6. `evidence`
7. `smoke_gate`

## Runtime Interpretation

- Executor responsibilities:
  - resolve the authoritative selected TECH package
  - assess which execution workstreams actually apply
  - derive the implementation task document and upstream design refs
  - derive optional frontend/backend/migration workstreams only when needed
  - derive the integration plan, evidence plan, and smoke-gate subject
  - emit one candidate package whose downstream target is `template.dev.feature_delivery_l2`
- Supervisor responsibilities:
  - verify the package stays at the implementation-entry layer
  - verify the workstream assessment matches emitted artifacts
  - verify the package carries enough structure that downstream execution does not need to reinterpret TECH scope
  - decide whether the package is execution-ready

## Boundary Rules

- Input must already be freeze-ready at the TECH layer.
- Output is a `feature_impl_candidate_package`, not a final code-delivery proof.
- `impl-task.md`, `upstream-design-refs.json`, `integration-plan.md`, `dev-evidence-plan.json`, and `smoke-gate-subject.json` are always mandatory.
- Frontend, backend, and migration workstreams are conditional and must be explicitly assessed.
- The package must preserve upstream FEAT and TECH lineage, with optional ARCH/API authority when present, but it must not create a new competing design truth source.

# Authoring Checklist

- Define the workflow boundary in plain language.
- Confirm input and output artifact types.
- Confirm authoritative source, runtime mode, and freeze expectations.
- Fill input and output contracts with explicit required fields and refs.
- For LEE Lite, generate a direct runtime entrypoint instead of defaulting to `lee run`.
- Update semantic checklists with workflow-specific risks.
- Keep executor and supervisor instructions separate.

# Review Checklist

- Does the skill keep a standard `SKILL.md` shell?
- Does `ll.contract.yaml` define roles, validations, evidence, lifecycle, and freeze gates?
- Are structural and semantic validations separate?
- Are execution and supervision evidence schemas present?
- Are role prompts split between executor and supervisor?
- Do placeholder scripts exist for input validation, output validation, evidence, and freeze guard?

---
artifact_type: feat_freeze_package
status: frozen
schema_version: 0.1.0
source_freeze_ref: FEAT_FREEZE_PACKAGE-001
---

# Example FEAT_FREEZE_PACKAGE

## Summary

Example upstream artifact.

## Scope

Example scope.

## Constraints

Example constraints.

---
artifact_type: feature_impl_candidate_package
status: accepted
schema_version: 0.1.0
source_refs:
  - FEAT_FREEZE_PACKAGE-001
---

# Example FEATURE_IMPL_CANDIDATE_PACKAGE

## Overview

Example governed output.

## Scope

Example output scope.

## Non-Goals

Example non-goals.

## Constraints

Example inherited constraints.

## Traceability

Map the output back to the source refs.

#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py collect-evidence --artifacts-dir "$1"

#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py freeze-guard --artifacts-dir "$1"

#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tech_to_impl_common import ensure_list, unique_strings
from tech_to_impl_derivation import (
    acceptance_checkpoints,
    assess_workstreams,
    backend_workstream_items,
    build_refs,
    consistency_check,
    deliverable_files,
    evidence_rows,
    frontend_workstream_items,
    implementation_scope,
    implementation_steps,
    integration_plan_items,
    migration_plan_items,
    risk_items,
)


DOWNSTREAM_TEMPLATE_ID = "template.dev.feature_delivery_l2"
DOWNSTREAM_TEMPLATE_PATH = "E:\\ai\\LEE\\spec-global\\departments\\dev\\workflows\\templates\\feature-delivery-l2-template.yaml"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _md_frontmatter(artifact_type: str, refs: dict[str, str | None], source_refs: list[str]) -> dict[str, Any]:
    payload = {
        "artifact_type": artifact_type,
        "status": "draft",
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "source_refs": source_refs,
    }
    if refs.get("arch_ref"):
        payload["arch_ref"] = refs["arch_ref"]
    if refs.get("api_ref"):
        payload["api_ref"] = refs["api_ref"]
    return payload


def build_candidate_package(package: Any, run_id: str) -> dict[str, Any]:
    feature = package.selected_feat
    refs = build_refs(package)
    assessment = assess_workstreams(feature, package)
    consistency = consistency_check(assessment)
    checkpoints = acceptance_checkpoints(feature)
    scope = implementation_scope(feature)
    steps = implementation_steps(feature, assessment)
    risks = risk_items(feature, assessment)
    deliverables = deliverable_files(assessment)
    integration_items = integration_plan_items(feature, assessment)
    evidence_plan_rows = evidence_rows(feature, assessment)
    frontend_items = frontend_workstream_items(feature)
    backend_items = backend_workstream_items(feature)
    migration_items = migration_plan_items(feature)

    source_refs = unique_strings(
        [f"dev.feat-to-tech::{package.run_id}", refs["feat_ref"], refs["tech_ref"]]
        + ensure_list(package.tech_json.get("source_refs"))
    )

    upstream_design_refs = {
        "artifact_type": "UPSTREAM_DESIGN_REFS",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "upstream_workflow_key": str(package.tech_json.get("workflow_key") or ""),
        "upstream_run_id": package.run_id,
        "primary_artifacts": {
            "tech_design_bundle": "tech-design-bundle.json",
            "tech_spec": "tech-spec.md",
            "tech_impl": "tech-impl.md",
            "arch_design": "arch-design.md" if refs["arch_ref"] else None,
            "api_contract": "api-contract.md" if refs["api_ref"] else None,
        },
        "frozen_source_refs": source_refs,
        "frozen_decisions": {
            "design_focus": ensure_list((package.tech_json.get("tech_design") or {}).get("design_focus")),
            "implementation_rules": ensure_list((package.tech_json.get("tech_design") or {}).get("implementation_rules")),
            "consistency_passed": bool((package.tech_json.get("design_consistency_check") or {}).get("passed")),
        },
    }

    handoff = {
        "handoff_id": f"handoff-{run_id}-to-feature-delivery",
        "from_skill": "ll-dev-tech-to-impl",
        "source_run_id": run_id,
        "target_template_id": DOWNSTREAM_TEMPLATE_ID,
        "target_template_path": DOWNSTREAM_TEMPLATE_PATH,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "primary_artifact_ref": "impl-bundle.json",
        "phase_inputs": {
            "implementation_task": ["impl-task.md"],
            "frontend": ["frontend-workstream.md"] if assessment["frontend_required"] else [],
            "backend": ["backend-workstream.md"] if assessment["backend_required"] else [],
            "migration": ["migration-cutover-plan.md"] if assessment["migration_required"] else [],
            "integration": ["integration-plan.md"],
            "evidence": ["dev-evidence-plan.json", "smoke-gate-subject.json"],
            "upstream_design": ["upstream-design-refs.json"],
        },
        "supporting_artifact_refs": deliverables,
        "created_at": utc_now(),
    }

    defects: list[dict[str, Any]] = []
    if not consistency["passed"]:
        defects.append(
            {
                "severity": "P1",
                "title": "No implementation surface selected",
                "detail": "; ".join(consistency["issues"]),
            }
        )

    bundle_json = {
        "artifact_type": "feature_impl_candidate_package",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "title": f"{feature.get('title') or refs['feat_ref']} Implementation Task Package",
        "status": "in_progress",
        "package_role": "candidate",
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "source_refs": source_refs,
        "selected_scope": {
            "title": feature.get("title"),
            "goal": feature.get("goal"),
            "scope": ensure_list(feature.get("scope")),
            "constraints": ensure_list(feature.get("constraints")),
            "dependencies": ensure_list(feature.get("dependencies")),
        },
        "workstream_assessment": assessment,
        "status_model": {
            "package": "in_progress",
            "smoke_gate": "pending_review",
        },
        "artifact_refs": {
            "bundle_markdown": "impl-bundle.md",
            "bundle_json": "impl-bundle.json",
            "impl_task": "impl-task.md",
            "upstream_design_refs": "upstream-design-refs.json",
            "frontend_workstream": "frontend-workstream.md" if assessment["frontend_required"] else None,
            "backend_workstream": "backend-workstream.md" if assessment["backend_required"] else None,
            "migration_cutover_plan": "migration-cutover-plan.md" if assessment["migration_required"] else None,
            "integration_plan": "integration-plan.md",
            "dev_evidence_plan": "dev-evidence-plan.json",
            "smoke_gate_subject": "smoke-gate-subject.json",
            "review_report": "impl-review-report.json",
            "acceptance_report": "impl-acceptance-report.json",
            "defect_list": "impl-defect-list.json",
            "handoff": "handoff-to-feature-delivery.json",
        },
        "upstream_design_refs": upstream_design_refs,
        "consistency_check": consistency,
        "downstream_handoff": handoff,
    }

    bundle_frontmatter = {
        "artifact_type": bundle_json["artifact_type"],
        "workflow_key": bundle_json["workflow_key"],
        "workflow_run_id": bundle_json["workflow_run_id"],
        "status": bundle_json["status"],
        "package_role": bundle_json["package_role"],
        "schema_version": bundle_json["schema_version"],
        "feat_ref": bundle_json["feat_ref"],
        "impl_ref": bundle_json["impl_ref"],
        "tech_ref": bundle_json["tech_ref"],
        "source_refs": bundle_json["source_refs"],
    }

    bundle_body = "\n\n".join(
        [
            f"# {bundle_json['title']}",
            "## Selected Upstream\n\n"
            + "\n".join(
                [
                    f"- feat_ref: `{refs['feat_ref']}`",
                    f"- tech_ref: `{refs['tech_ref']}`",
                    f"- arch_ref: `{refs['arch_ref']}`" if refs["arch_ref"] else "- arch_ref: not present",
                    f"- api_ref: `{refs['api_ref']}`" if refs["api_ref"] else "- api_ref: not present",
                    f"- title: {feature.get('title')}",
                    f"- goal: {feature.get('goal')}",
                ]
            ),
            "## Applicability Assessment\n\n"
            + "\n".join(
                [
                    f"- frontend_required: {assessment['frontend_required']}",
                    *[f"  - {item}" for item in assessment["rationale"]["frontend"]],
                    f"- backend_required: {assessment['backend_required']}",
                    *[f"  - {item}" for item in assessment["rationale"]["backend"]],
                    f"- migration_required: {assessment['migration_required']}",
                    *[f"  - {item}" for item in assessment["rationale"]["migration"]],
                ]
            ),
            "## Implementation Task\n\n"
            + "\n".join([f"- {index}. {step['title']}: {step['done_when']}" for index, step in enumerate(steps, start=1)]),
            "## Integration Plan\n\n" + "\n".join(f"- {item}" for item in integration_items),
            "## Evidence Plan\n\n" + "\n".join(f"- {row['acceptance_ref']}: {', '.join(row['evidence_types'])}" for row in evidence_plan_rows),
            "## Smoke Gate Subject\n\n- ready_for_execution remains false until supervisor review passes.",
            "## Delivery Handoff\n\n"
            + "\n".join(
                [
                    f"- target_template_id: `{DOWNSTREAM_TEMPLATE_ID}`",
                    f"- primary_artifact_ref: `{handoff['primary_artifact_ref']}`",
                    f"- phase_inputs: {', '.join(sorted(handoff['phase_inputs'].keys()))}",
                ]
            ),
            "## Traceability\n\n" + "\n".join(f"- {item}" for item in source_refs),
        ]
    )

    impl_task_body = "\n\n".join(
        [
            f"# {refs['impl_ref']}",
            "## 1. 目标\n\n"
            + "\n".join(
                [
                    f"- 覆盖目标: {feature.get('goal')}",
                    "- 不覆盖内容: 不在 IMPL 中重写上游 TECH/ARCH/API 决策，只组织实施、接线、迁移与验收。",
                ]
            ),
            "## 2. 上游依赖\n\n"
            + "\n".join(
                [
                    f"- FEAT: `{refs['feat_ref']}`",
                    f"- TECH: `{refs['tech_ref']}`",
                    f"- ARCH: `{refs['arch_ref']}`" if refs["arch_ref"] else "- ARCH: not present",
                    f"- API: `{refs['api_ref']}`" if refs["api_ref"] else "- API: not present",
                    "- 继承规则: 上游冻结决策只能被实现和验证，不能在 IMPL 中被改写。",
                ]
            ),
            "## 3. 实施范围\n\n" + "\n".join(f"- {item}" for item in scope),
            "## 4. 实施步骤\n\n"
            + "\n".join(
                [
                    f"### Step {index}: {step['title']}\n- 工作内容: {step['work']}\n- 完成条件: {step['done_when']}"
                    for index, step in enumerate(steps, start=1)
                ]
            ),
            "## 5. 风险与阻塞\n\n" + "\n".join(f"- {item}" for item in risks),
            "## 6. 交付物\n\n" + "\n".join(f"- {item}" for item in deliverables),
            "## 7. 验收检查点\n\n"
            + "\n".join(f"- {item['ref']}: {item['scenario']} -> {item['expectation']}" for item in checkpoints),
        ]
    )

    integration_body = "\n\n".join(
        [
            f"# INTEGRATION-{refs['impl_ref']}",
            "## Integration Sequence\n\n" + "\n".join(f"- {item}" for item in integration_items),
            "## Blocking Conditions\n\n"
            + "\n".join(
                [
                    "- Upstream refs must remain resolvable.",
                    "- Optional workstreams can only enter execution if their applicability assessment is true.",
                    "- Smoke review is blocked until evidence plan artifacts are available.",
                ]
            ),
        ]
    )

    frontend_body = None
    if assessment["frontend_required"]:
        frontend_body = "\n\n".join(
            [
                f"# FRONTEND-{refs['impl_ref']}",
                "## Frontend Surface\n\n" + "\n".join(f"- {item}" for item in frontend_items),
                "## Done Criteria\n\n- Frontend implementation stays inside the selected IMPL boundary and traceability chain.",
            ]
        )

    backend_body = None
    if assessment["backend_required"]:
        backend_body = "\n\n".join(
            [
                f"# BACKEND-{refs['impl_ref']}",
                "## Backend Surface\n\n" + "\n".join(f"- {item}" for item in backend_items),
                "## Done Criteria\n\n- Backend changes satisfy frozen TECH/ARCH/API decisions without introducing new design truth.",
            ]
        )

    migration_body = None
    if assessment["migration_required"]:
        migration_body = "\n\n".join(
            [
                f"# MIGRATION-{refs['impl_ref']}",
                "## Migration and Cutover\n\n" + "\n".join(f"- {item}" for item in migration_items),
                "## Done Criteria\n\n- Rollout and rollback expectations are explicit enough for downstream execution.",
            ]
        )

    smoke_gate_subject = {
        "artifact_type": "SMOKE_GATE_SUBJECT",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "gate_ref": f"SMOKE-GATE-{refs['impl_ref']}",
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "status": "pending_review",
        "decision": "pending",
        "ready_for_execution": False,
        "required_inputs": ["impl-task.md", "integration-plan.md", "dev-evidence-plan.json"],
        "acceptance_refs": [item["ref"] for item in checkpoints],
        "created_at": utc_now(),
    }

    evidence_plan = {
        "artifact_type": "DEV_EVIDENCE_PLAN",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "rows": evidence_plan_rows,
        "status": "draft",
    }

    review_report = {
        "report_id": f"impl-review-{run_id}",
        "report_type": "feature_impl_review",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "status": "pending",
        "decision": "pending",
        "summary": "Pending supervisor review.",
        "findings": [],
        "created_at": utc_now(),
    }

    acceptance_report = {
        "report_id": f"impl-acceptance-{run_id}",
        "report_type": "feature_impl_acceptance",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "status": "pending",
        "decision": "pending",
        "summary": "Pending supervisor review.",
        "acceptance_findings": [],
        "created_at": utc_now(),
    }

    return {
        "refs": refs,
        "assessment": assessment,
        "consistency": consistency,
        "bundle_frontmatter": bundle_frontmatter,
        "bundle_body": bundle_body,
        "bundle_json": bundle_json,
        "impl_task_frontmatter": _md_frontmatter("IMPL_TASK", refs, source_refs),
        "impl_task_body": impl_task_body,
        "upstream_design_refs": upstream_design_refs,
        "integration_frontmatter": _md_frontmatter("INTEGRATION_PLAN", refs, source_refs),
        "integration_body": integration_body,
        "frontend_frontmatter": _md_frontmatter("FRONTEND_WORKSTREAM", refs, source_refs) if frontend_body else None,
        "frontend_body": frontend_body,
        "backend_frontmatter": _md_frontmatter("BACKEND_WORKSTREAM", refs, source_refs) if backend_body else None,
        "backend_body": backend_body,
        "migration_frontmatter": _md_frontmatter("MIGRATION_CUTOVER_PLAN", refs, source_refs) if migration_body else None,
        "migration_body": migration_body,
        "evidence_plan": evidence_plan,
        "smoke_gate_subject": smoke_gate_subject,
        "review_report": review_report,
        "acceptance_report": acceptance_report,
        "defect_list": defects,
        "handoff": handoff,
        "execution_decisions": [
            f"Selected TECH package {refs['tech_ref']} from upstream run {package.run_id}.",
            f"frontend_required={assessment['frontend_required']}, backend_required={assessment['backend_required']}, migration_required={assessment['migration_required']}.",
            f"Prepared downstream handoff to {DOWNSTREAM_TEMPLATE_ID}.",
        ],
        "execution_uncertainties": consistency["issues"][:],
    }

#!/usr/bin/env python3
"""
Shared helpers for the lite-native tech-to-impl runtime.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_INPUT_FILES = [
    "package-manifest.json",
    "tech-design-bundle.md",
    "tech-design-bundle.json",
    "tech-spec.md",
    "tech-impl.md",
    "tech-review-report.json",
    "tech-acceptance-report.json",
    "tech-defect-list.json",
    "tech-freeze-gate.json",
    "handoff-to-tech-impl.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_markdown_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    if not markdown_text.startswith("---\n"):
        return {}, markdown_text
    end_marker = "\n---\n"
    end_index = markdown_text.find(end_marker, 4)
    if end_index == -1:
        return {}, markdown_text
    frontmatter_text = markdown_text[4:end_index]
    body = markdown_text[end_index + len(end_marker) :]
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        return {}, body
    return data, body


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized or "unspecified"


def guess_repo_root_from_input(input_path: Path) -> Path:
    parts = list(input_path.parts)
    for index, part in enumerate(parts):
        if part.lower() == "artifacts" and index > 0:
            return Path(*parts[:index])
    return input_path.parent


@dataclass
class TechPackage:
    artifacts_dir: Path
    manifest: dict[str, Any]
    tech_json: dict[str, Any]
    tech_frontmatter: dict[str, Any]
    tech_markdown_body: str
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    execution_evidence: dict[str, Any]
    supervision_evidence: dict[str, Any]
    gate: dict[str, Any]
    handoff: dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(self.tech_json.get("workflow_run_id") or self.manifest.get("run_id") or self.artifacts_dir.name)

    @property
    def feat_ref(self) -> str:
        return str(self.tech_json.get("feat_ref") or "").strip()

    @property
    def tech_ref(self) -> str:
        return str(self.tech_json.get("tech_ref") or "").strip()

    @property
    def arch_ref(self) -> str | None:
        value = str(self.tech_json.get("arch_ref") or "").strip()
        return value or None

    @property
    def api_ref(self) -> str | None:
        value = str(self.tech_json.get("api_ref") or "").strip()
        return value or None

    @property
    def selected_feat(self) -> dict[str, Any]:
        selected = self.tech_json.get("selected_feat") or {}
        return selected if isinstance(selected, dict) else {}


def load_tech_package(artifacts_dir: Path) -> TechPackage:
    markdown_text = (artifacts_dir / "tech-design-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    return TechPackage(
        artifacts_dir=artifacts_dir,
        manifest=load_json(artifacts_dir / "package-manifest.json"),
        tech_json=load_json(artifacts_dir / "tech-design-bundle.json"),
        tech_frontmatter=frontmatter,
        tech_markdown_body=body,
        review_report=load_json(artifacts_dir / "tech-review-report.json"),
        acceptance_report=load_json(artifacts_dir / "tech-acceptance-report.json"),
        defect_list=load_json(artifacts_dir / "tech-defect-list.json"),
        execution_evidence=load_json(artifacts_dir / "execution-evidence.json"),
        supervision_evidence=load_json(artifacts_dir / "supervision-evidence.json"),
        gate=load_json(artifacts_dir / "tech-freeze-gate.json"),
        handoff=load_json(artifacts_dir / "handoff-to-tech-impl.json"),
    )


def validate_input_package(artifacts_dir: Path, feat_ref: str, tech_ref: str) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Input package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_INPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required input artifact: {required_file}")

    if not feat_ref.strip():
        errors.append("feat_ref is required.")
    if not tech_ref.strip():
        errors.append("tech_ref is required.")
    if errors:
        return errors, {"valid": False, "missing_files": errors}

    package = load_tech_package(artifacts_dir)
    bundle = package.tech_json
    selected_feat = package.selected_feat

    artifact_type = str(bundle.get("artifact_type") or "")
    if artifact_type != "tech_design_package":
        errors.append(f"tech-design-bundle.json artifact_type must be tech_design_package, got: {artifact_type or '<missing>'}")

    workflow_key = str(bundle.get("workflow_key") or package.gate.get("workflow_key") or "")
    if workflow_key != "dev.feat-to-tech":
        errors.append(f"Upstream workflow must be dev.feat-to-tech, got: {workflow_key or '<missing>'}")

    status = str(bundle.get("status") or package.manifest.get("status") or "")
    if status not in {"accepted", "frozen"}:
        errors.append(f"tech-design status must be accepted or frozen, got: {status or '<missing>'}")

    if package.gate.get("freeze_ready") is not True:
        errors.append("tech-freeze-gate.json must mark the package as freeze_ready.")

    if package.feat_ref != feat_ref.strip():
        errors.append(f"Selected feat_ref does not match tech-design-bundle.json: {feat_ref}")
    if package.tech_ref != tech_ref.strip():
        errors.append(f"Selected tech_ref does not match tech-design-bundle.json: {tech_ref}")

    selected_feat_ref = str(selected_feat.get("feat_ref") or "").strip()
    if selected_feat_ref and selected_feat_ref != feat_ref.strip():
        errors.append("selected_feat.feat_ref must match the selected feat_ref.")
    for field in ["title", "goal", "scope", "constraints"]:
        if selected_feat.get(field) in (None, "", []):
            errors.append(f"selected_feat is missing required field: {field}")

    source_refs = ensure_list(bundle.get("source_refs"))
    for prefix in ["FEAT-", "EPIC-", "SRC-"]:
        if not any(ref.startswith(prefix) for ref in source_refs):
            errors.append(f"tech-design-bundle.json source_refs must include {prefix}.")
    if tech_ref.strip() not in source_refs and package.tech_ref not in source_refs:
        errors.append("tech-design-bundle.json source_refs must retain the selected TECH ref.")

    if bool(bundle.get("arch_required")):
        if not package.arch_ref:
            errors.append("arch_required is true but arch_ref is missing.")
        if not (artifacts_dir / "arch-design.md").exists():
            errors.append("arch_required is true but arch-design.md is missing.")
    if bool(bundle.get("api_required")):
        if not package.api_ref:
            errors.append("api_required is true but api_ref is missing.")
        if not (artifacts_dir / "api-contract.md").exists():
            errors.append("api_required is true but api-contract.md is missing.")

    if str(package.handoff.get("target_workflow") or "") != "workflow.dev.tech_to_impl":
        errors.append("handoff-to-tech-impl.json must preserve workflow.dev.tech_to_impl lineage.")

    result = {
        "valid": not errors,
        "run_id": package.run_id,
        "workflow_key": workflow_key,
        "status": status,
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "arch_ref": package.arch_ref,
        "api_ref": package.api_ref,
        "feat_title": str(selected_feat.get("title") or ""),
        "source_refs": source_refs,
    }
    return errors, result

#!/usr/bin/env python3
"""
Derivation helpers for the lite-native tech-to-impl runtime.
"""

from __future__ import annotations

from typing import Any

from tech_to_impl_common import ensure_list, unique_strings


FRONTEND_KEYWORDS = [
    "ui",
    "ux",
    "page",
    "screen",
    "view",
    "component",
    "frontend",
    "front-end",
    "页面",
    "交互",
    "前端",
    "组件",
    "文案",
]

BACKEND_KEYWORDS = [
    "backend",
    "service",
    "worker",
    "job",
    "api",
    "contract",
    "schema",
    "database",
    "storage",
    "queue",
    "event",
    "message",
    "gate",
    "workflow",
    "runtime",
    "path",
    "io",
    "registry",
    "后端",
    "服务",
    "接口",
    "契约",
    "数据库",
    "事件",
    "消息",
    "发布",
]

MIGRATION_KEYWORDS = [
    "migration",
    "cutover",
    "rollout",
    "fallback",
    "rollback",
    "compat",
    "切换",
    "迁移",
    "灰度",
    "回滚",
    "兼容",
]

NEGATION_MARKERS = ["不", "无", "without", "no ", "not ", "do not", "must not"]


def feature_segments(feature: dict[str, Any]) -> list[str]:
    segments: list[str] = []
    for key in ["title", "goal"]:
        value = str(feature.get(key) or "").strip()
        if value:
            segments.append(value)
    for key in ["scope", "constraints", "dependencies"]:
        segments.extend(ensure_list(feature.get(key)))
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            segments.extend(
                [
                    str(check.get("scenario") or ""),
                    str(check.get("given") or ""),
                    str(check.get("when") or ""),
                    str(check.get("then") or ""),
                ]
            )
    return [segment for segment in segments if segment.strip()]


def keyword_hits(feature: dict[str, Any], keywords: list[str]) -> list[str]:
    hits: list[str] = []
    for segment in feature_segments(feature):
        lowered = segment.lower()
        if any(marker in lowered for marker in NEGATION_MARKERS):
            continue
        for keyword in keywords:
            if keyword in lowered and keyword not in hits:
                hits.append(keyword)
    return hits


def build_refs(package: Any) -> dict[str, str | None]:
    tech_ref = package.tech_ref
    impl_ref = tech_ref.replace("TECH-", "IMPL-", 1) if tech_ref.startswith("TECH-") else f"IMPL-{package.feat_ref}"
    return {
        "feat_ref": package.feat_ref,
        "tech_ref": tech_ref,
        "impl_ref": impl_ref,
        "arch_ref": package.arch_ref,
        "api_ref": package.api_ref,
    }


def assess_workstreams(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    frontend_hits = keyword_hits(feature, FRONTEND_KEYWORDS)
    backend_hits = keyword_hits(feature, BACKEND_KEYWORDS)
    migration_hits = keyword_hits(feature, MIGRATION_KEYWORDS)

    frontend_rationale = (
        [f"Detected explicit UI or interaction surface: {', '.join(frontend_hits[:4])}."]
        if frontend_hits
        else ["No explicit UI/page/component implementation surface was detected."]
    )

    backend_rationale: list[str] = []
    if backend_hits:
        backend_rationale.append(f"Detected runtime/service/contract surface: {', '.join(backend_hits[:4])}.")
    if bool(package.tech_json.get("api_required")) and not backend_hits:
        backend_rationale.append("Upstream TECH package already requires API/contract implementation support.")
    if bool(package.tech_json.get("arch_required")) and not backend_hits:
        backend_rationale.append("Upstream TECH package already requires architecture-aligned execution work.")
    if not backend_rationale:
        backend_rationale.append("No runtime/service/storage/workflow implementation surface was detected.")

    migration_rationale = (
        [f"Detected migration/cutover language: {', '.join(migration_hits[:4])}."]
        if migration_hits
        else ["No migration, cutover, rollback, or compat-mode surface was detected."]
    )

    frontend_required = bool(frontend_hits)
    backend_required = bool(backend_hits) or bool(package.tech_json.get("api_required")) or bool(package.tech_json.get("arch_required"))
    migration_required = bool(migration_hits)

    return {
        "frontend_required": frontend_required,
        "backend_required": backend_required,
        "migration_required": migration_required,
        "execution_surface_count": int(frontend_required) + int(backend_required),
        "rationale": {
            "frontend": frontend_rationale,
            "backend": backend_rationale,
            "migration": migration_rationale,
        },
    }


def implementation_scope(feature: dict[str, Any]) -> list[str]:
    scope = ensure_list(feature.get("scope"))[:4]
    constraints = ensure_list(feature.get("constraints"))[:2]
    return unique_strings(scope + constraints)[:6]


def implementation_steps(feature: dict[str, Any], assessment: dict[str, Any]) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = [
        {
            "title": "Freeze upstream refs and implementation boundary",
            "work": "Align feat_ref, tech_ref, optional arch/api refs, file touch scope, and blocked conditions before touching execution surfaces.",
            "done_when": "The implementation entry uses only frozen upstream refs and does not redefine technical decisions.",
        }
    ]
    if assessment["frontend_required"]:
        steps.append(
            {
                "title": "Implement frontend surface",
                "work": "Apply the selected UI/page/component changes and keep interaction behavior aligned to the frozen TECH/API boundary.",
                "done_when": "Frontend changes are wired, bounded to the selected scope, and traceable to acceptance checks.",
            }
        )
    if assessment["backend_required"]:
        steps.append(
            {
                "title": "Implement backend and contract surface",
                "work": "Apply runtime/service/storage/workflow/contract changes required by the selected TECH package.",
                "done_when": "Backend-side changes satisfy the selected technical design without introducing shadow design drift.",
            }
        )
    if assessment["migration_required"]:
        steps.append(
            {
                "title": "Prepare migration and cutover controls",
                "work": "Define rollout, rollback, compat-mode, or cutover sequencing needed to land the change safely.",
                "done_when": "Migration prerequisites, guardrails, and fallback actions are explicit enough for downstream execution.",
            }
        )
    steps.append(
        {
            "title": "Integrate, evidence, and handoff",
            "work": "Complete integration ordering, evidence collection hooks, smoke subject packaging, and downstream handoff.",
            "done_when": "The package can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries.",
        }
    )
    return steps


def risk_items(feature: dict[str, Any], assessment: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("constraints"))[:3] + ensure_list(feature.get("dependencies"))[:2]
    if assessment["migration_required"]:
        items.append("Migration or cutover requires an explicit rollback or compat-mode path.")
    return unique_strings(items)[:6]


def deliverable_files(assessment: dict[str, Any]) -> list[str]:
    deliverables = [
        "impl-bundle.md",
        "impl-bundle.json",
        "impl-task.md",
        "upstream-design-refs.json",
        "integration-plan.md",
        "dev-evidence-plan.json",
        "smoke-gate-subject.json",
        "impl-review-report.json",
        "impl-acceptance-report.json",
        "impl-defect-list.json",
        "handoff-to-feature-delivery.json",
        "execution-evidence.json",
        "supervision-evidence.json",
    ]
    if assessment["frontend_required"]:
        deliverables.append("frontend-workstream.md")
    if assessment["backend_required"]:
        deliverables.append("backend-workstream.md")
    if assessment["migration_required"]:
        deliverables.append("migration-cutover-plan.md")
    return deliverables


def acceptance_checkpoints(feature: dict[str, Any]) -> list[dict[str, str]]:
    checkpoints: list[dict[str, str]] = []
    for index, check in enumerate(feature.get("acceptance_checks") or [], start=1):
        if not isinstance(check, dict):
            continue
        checkpoints.append(
            {
                "ref": f"AC-{index:03d}",
                "scenario": str(check.get("scenario") or "").strip() or f"acceptance-{index}",
                "expectation": str(check.get("then") or "").strip() or "Expectation must be confirmed during execution.",
            }
        )
    return checkpoints


def integration_plan_items(feature: dict[str, Any], assessment: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("dependencies"))[:3]
    if assessment["frontend_required"] and assessment["backend_required"]:
        items.append("Freeze frontend/backend integration order before smoke review.")
    if assessment["migration_required"]:
        items.append("Migration or cutover can execute only after implementation evidence is complete.")
    if not items:
        items.append("Single-surface execution still preserves one explicit integration checkpoint before smoke review.")
    return unique_strings(items)[:5]


def evidence_rows(feature: dict[str, Any], assessment: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_types: list[str] = []
    if assessment["frontend_required"]:
        evidence_types.append("frontend-verification")
    if assessment["backend_required"]:
        evidence_types.append("backend-verification")
    if assessment["migration_required"]:
        evidence_types.append("migration-verification")
    evidence_types.append("smoke-review-input")

    rows: list[dict[str, Any]] = []
    for checkpoint in acceptance_checkpoints(feature):
        rows.append(
            {
                "acceptance_ref": checkpoint["ref"],
                "scenario": checkpoint["scenario"],
                "evidence_types": evidence_types,
            }
        )
    return rows


def frontend_workstream_items(feature: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("scope"))[:3]
    for checkpoint in acceptance_checkpoints(feature):
        items.append(f"{checkpoint['ref']}: {checkpoint['scenario']} -> {checkpoint['expectation']}")
    return unique_strings(items)[:5]


def backend_workstream_items(feature: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("constraints"))[:3] + ensure_list(feature.get("dependencies"))[:2]
    return unique_strings(items or ensure_list(feature.get("scope"))[:4])[:5]


def migration_plan_items(feature: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("constraints"))[:2] + ensure_list(feature.get("dependencies"))[:2]
    items.append("Define rollback or compat-mode behavior if the rollout path cannot complete cleanly.")
    return unique_strings(items)[:5]


def consistency_check(assessment: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    issues: list[str] = []

    surface_selected = assessment["frontend_required"] or assessment["backend_required"]
    checks.append(
        {
            "name": "Execution surface selected",
            "passed": surface_selected,
            "detail": "At least one frontend or backend execution surface must be present.",
        }
    )
    if not surface_selected:
        issues.append("The selected TECH package exposes no executable frontend or backend workstream.")

    checks.append(
        {
            "name": "Migration is conditional",
            "passed": True,
            "detail": "Migration or cutover planning remains conditional instead of unconditional output.",
        }
    )

    return {
        "passed": not issues,
        "checks": checks,
        "issues": issues,
    }

#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from tech_to_impl_builder import DOWNSTREAM_TEMPLATE_ID, DOWNSTREAM_TEMPLATE_PATH
from tech_to_impl_common import dump_json, ensure_list, load_json, parse_markdown_frontmatter, render_markdown

REQUIRED_OUTPUT_FILES = [
    "package-manifest.json",
    "impl-bundle.md",
    "impl-bundle.json",
    "impl-task.md",
    "upstream-design-refs.json",
    "integration-plan.md",
    "dev-evidence-plan.json",
    "smoke-gate-subject.json",
    "impl-review-report.json",
    "impl-acceptance-report.json",
    "impl-defect-list.json",
    "handoff-to-feature-delivery.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
REQUIRED_BUNDLE_HEADINGS = [
    "Selected Upstream",
    "Applicability Assessment",
    "Implementation Task",
    "Integration Plan",
    "Evidence Plan",
    "Smoke Gate Subject",
    "Delivery Handoff",
    "Traceability",
]
REQUIRED_IMPL_TASK_HEADINGS = [
    "## 1. 目标",
    "## 2. 上游依赖",
    "## 3. 实施范围",
    "## 4. 实施步骤",
    "## 5. 风险与阻塞",
    "## 6. 交付物",
    "## 7. 验收检查点",
]


def write_markdown(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(frontmatter, body), encoding="utf-8")


def write_executor_outputs(output_dir: Path, package: Any, generated: dict[str, Any], command_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_markdown(output_dir / "impl-bundle.md", generated["bundle_frontmatter"], generated["bundle_body"])
    dump_json(output_dir / "impl-bundle.json", generated["bundle_json"])
    write_markdown(output_dir / "impl-task.md", generated["impl_task_frontmatter"], generated["impl_task_body"])
    dump_json(output_dir / "upstream-design-refs.json", generated["upstream_design_refs"])
    write_markdown(output_dir / "integration-plan.md", generated["integration_frontmatter"], generated["integration_body"])
    dump_json(output_dir / "dev-evidence-plan.json", generated["evidence_plan"])
    dump_json(output_dir / "smoke-gate-subject.json", generated["smoke_gate_subject"])
    dump_json(output_dir / "impl-review-report.json", generated["review_report"])
    dump_json(output_dir / "impl-acceptance-report.json", generated["acceptance_report"])
    dump_json(output_dir / "impl-defect-list.json", generated["defect_list"])
    dump_json(output_dir / "handoff-to-feature-delivery.json", generated["handoff"])

    optional_markdown = [
        ("frontend-workstream.md", generated["frontend_frontmatter"], generated["frontend_body"]),
        ("backend-workstream.md", generated["backend_frontmatter"], generated["backend_body"]),
        ("migration-cutover-plan.md", generated["migration_frontmatter"], generated["migration_body"]),
    ]
    for name, frontmatter, body in optional_markdown:
        path = output_dir / name
        if frontmatter and body:
            write_markdown(path, frontmatter, body)
        elif path.exists():
            path.unlink()

    outputs = [str(output_dir / name) for name in REQUIRED_OUTPUT_FILES if name != "supervision-evidence.json"]
    for name, frontmatter, _ in optional_markdown:
        if frontmatter:
            outputs.append(str(output_dir / name))

    dump_json(
        output_dir / "package-manifest.json",
        {
            "run_id": generated["bundle_json"]["workflow_run_id"],
            "workflow_key": "dev.tech-to-impl",
            "artifacts_dir": str(output_dir),
            "input_artifacts_dir": str(package.artifacts_dir),
            "feat_ref": generated["bundle_json"]["feat_ref"],
            "tech_ref": generated["bundle_json"]["tech_ref"],
            "impl_ref": generated["bundle_json"]["impl_ref"],
            "status": generated["bundle_json"]["status"],
            "primary_artifact_ref": str(output_dir / "impl-bundle.json"),
            "review_report_ref": str(output_dir / "impl-review-report.json"),
            "acceptance_report_ref": str(output_dir / "impl-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "impl-defect-list.json"),
            "smoke_gate_subject_ref": str(output_dir / "smoke-gate-subject.json"),
            "handoff_ref": str(output_dir / "handoff-to-feature-delivery.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
        },
    )
    dump_json(
        output_dir / "execution-evidence.json",
        {
            "skill_id": "ll-dev-tech-to-impl",
            "run_id": generated["bundle_json"]["workflow_run_id"],
            "role": "executor",
            "inputs": [str(package.artifacts_dir), generated["bundle_json"]["feat_ref"], generated["bundle_json"]["tech_ref"]],
            "outputs": outputs,
            "commands_run": [command_name],
            "structural_results": {
                "input_validation": "pass",
                "impl_task_present": True,
                "upstream_design_refs_present": True,
                "frontend_required": generated["assessment"]["frontend_required"],
                "backend_required": generated["assessment"]["backend_required"],
                "migration_required": generated["assessment"]["migration_required"],
                "consistency_passed": generated["consistency"]["passed"],
            },
            "key_decisions": generated["execution_decisions"],
            "uncertainties": generated["execution_uncertainties"],
        },
    )
    dump_json(
        output_dir / "supervision-evidence.json",
        {
            "skill_id": "ll-dev-tech-to-impl",
            "run_id": generated["bundle_json"]["workflow_run_id"],
            "role": "supervisor",
            "reviewed_inputs": [str(output_dir / "impl-bundle.md"), str(output_dir / "impl-bundle.json")],
            "reviewed_outputs": [str(output_dir / "impl-task.md"), str(output_dir / "integration-plan.md")],
            "semantic_findings": [],
            "decision": "revise",
            "reason": "Pending supervisor review.",
        },
    )


def build_supervision_evidence(artifacts_dir: Path) -> dict[str, Any]:
    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    handoff = load_json(artifacts_dir / "handoff-to-feature-delivery.json")
    upstream_refs = load_json(artifacts_dir / "upstream-design-refs.json")
    findings: list[dict[str, Any]] = []

    assessment = bundle_json.get("workstream_assessment") or {}
    frontend_required = bool(assessment.get("frontend_required"))
    backend_required = bool(assessment.get("backend_required"))
    migration_required = bool(assessment.get("migration_required"))

    if handoff.get("target_template_id") != DOWNSTREAM_TEMPLATE_ID:
        findings.append({"severity": "P1", "title": "Wrong downstream template target", "detail": f"Handoff must target {DOWNSTREAM_TEMPLATE_ID}."})
    if handoff.get("target_template_path") != DOWNSTREAM_TEMPLATE_PATH:
        findings.append({"severity": "P1", "title": "Wrong downstream template path", "detail": "Handoff target_template_path is inconsistent."})
    if not (frontend_required or backend_required):
        findings.append({"severity": "P1", "title": "No execution surface selected", "detail": "At least one frontend or backend workstream must be present."})
    if frontend_required and not (artifacts_dir / "frontend-workstream.md").exists():
        findings.append({"severity": "P1", "title": "Missing frontend workstream", "detail": "frontend_required is true but frontend-workstream.md is missing."})
    if backend_required and not (artifacts_dir / "backend-workstream.md").exists():
        findings.append({"severity": "P1", "title": "Missing backend workstream", "detail": "backend_required is true but backend-workstream.md is missing."})
    if migration_required and not (artifacts_dir / "migration-cutover-plan.md").exists():
        findings.append({"severity": "P1", "title": "Missing migration plan", "detail": "migration_required is true but migration-cutover-plan.md is missing."})
    if str(upstream_refs.get("feat_ref") or "") != str(bundle_json.get("feat_ref") or ""):
        findings.append({"severity": "P1", "title": "Upstream FEAT mismatch", "detail": "upstream-design-refs.json must retain the selected feat_ref."})
    if str(upstream_refs.get("tech_ref") or "") != str(bundle_json.get("tech_ref") or ""):
        findings.append({"severity": "P1", "title": "Upstream TECH mismatch", "detail": "upstream-design-refs.json must retain the selected tech_ref."})

    blocking = [item for item in findings if str(item.get("severity") or "") in {"P0", "P1"}]
    passed = not blocking
    return {
        "skill_id": "ll-dev-tech-to-impl",
        "run_id": str(bundle_json.get("workflow_run_id") or artifacts_dir.name),
        "role": "supervisor",
        "reviewed_inputs": [
            str(artifacts_dir / "impl-bundle.md"),
            str(artifacts_dir / "impl-bundle.json"),
            str(artifacts_dir / "upstream-design-refs.json"),
        ],
        "reviewed_outputs": [
            str(artifacts_dir / "impl-task.md"),
            str(artifacts_dir / "integration-plan.md"),
            str(artifacts_dir / "handoff-to-feature-delivery.json"),
        ],
        "semantic_findings": findings,
        "decision": "pass" if passed else "revise",
        "reason": "Implementation task package is ready for downstream execution." if passed else "Implementation task package requires revision before downstream execution.",
    }


def update_supervisor_outputs(artifacts_dir: Path, supervision: dict[str, Any]) -> None:
    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    review_report = load_json(artifacts_dir / "impl-review-report.json")
    acceptance_report = load_json(artifacts_dir / "impl-acceptance-report.json")
    smoke_gate_subject = load_json(artifacts_dir / "smoke-gate-subject.json")

    blocking = [item for item in supervision.get("semantic_findings") or [] if str(item.get("severity") or "") in {"P0", "P1"}]
    passed = supervision.get("decision") == "pass"
    bundle_status = "execution_ready" if passed else "blocked"

    bundle_json["status"] = bundle_status
    bundle_json["status_model"] = {"package": bundle_status, "smoke_gate": "pending_execution" if passed else "blocked"}
    manifest["status"] = bundle_status

    review_report.update(
        {
            "status": "completed",
            "decision": "pass" if passed else "revise",
            "summary": "Implementation task review passed." if passed else "Implementation task review requires revision.",
            "findings": supervision.get("semantic_findings") or [],
        }
    )
    acceptance_report.update(
        {
            "status": "completed",
            "decision": "approve" if passed else "revise",
            "summary": "Candidate package satisfies downstream execution entry conditions." if passed else "Candidate package does not yet satisfy downstream execution entry conditions.",
            "acceptance_findings": blocking,
        }
    )
    smoke_gate_subject.update(
        {
            "status": "pending_execution" if passed else "blocked",
            "decision": "ready" if passed else "revise",
            "ready_for_execution": passed,
        }
    )

    frontmatter, body = parse_markdown_frontmatter((artifacts_dir / "impl-bundle.md").read_text(encoding="utf-8"))
    frontmatter["status"] = bundle_status
    (artifacts_dir / "impl-bundle.md").write_text(render_markdown(frontmatter, body), encoding="utf-8")

    dump_json(artifacts_dir / "impl-bundle.json", bundle_json)
    dump_json(artifacts_dir / "impl-review-report.json", review_report)
    dump_json(artifacts_dir / "impl-acceptance-report.json", acceptance_report)
    dump_json(artifacts_dir / "impl-defect-list.json", supervision.get("semantic_findings") or [])
    dump_json(artifacts_dir / "smoke-gate-subject.json", smoke_gate_subject)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "package-manifest.json", manifest)


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Output package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_OUTPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required output artifact: {required_file}")
    if errors:
        return errors, {"valid": False}

    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    handoff = load_json(artifacts_dir / "handoff-to-feature-delivery.json")
    upstream_refs = load_json(artifacts_dir / "upstream-design-refs.json")

    if bundle_json.get("artifact_type") != "feature_impl_candidate_package":
        errors.append("impl-bundle.json artifact_type must be feature_impl_candidate_package.")
    if bundle_json.get("workflow_key") != "dev.tech-to-impl":
        errors.append("impl-bundle.json workflow_key must be dev.tech-to-impl.")
    if bundle_json.get("package_role") != "candidate":
        errors.append("impl-bundle.json package_role must be candidate.")

    source_refs = ensure_list(bundle_json.get("source_refs"))
    for prefix in ["dev.feat-to-tech::", "FEAT-", "TECH-", "EPIC-", "SRC-"]:
        if not any(ref.startswith(prefix) for ref in source_refs):
            errors.append(f"impl-bundle.json source_refs must include {prefix}.")

    _, bundle_body = parse_markdown_frontmatter((artifacts_dir / "impl-bundle.md").read_text(encoding="utf-8"))
    for heading in REQUIRED_BUNDLE_HEADINGS:
        if f"## {heading}" not in bundle_body:
            errors.append(f"impl-bundle.md is missing section: {heading}")

    _, impl_task_body = parse_markdown_frontmatter((artifacts_dir / "impl-task.md").read_text(encoding="utf-8"))
    for heading in REQUIRED_IMPL_TASK_HEADINGS:
        if heading not in impl_task_body:
            errors.append(f"impl-task.md is missing section: {heading}")

    assessment = bundle_json.get("workstream_assessment") or {}
    frontend_required = bool(assessment.get("frontend_required"))
    backend_required = bool(assessment.get("backend_required"))
    migration_required = bool(assessment.get("migration_required"))

    if frontend_required and not (artifacts_dir / "frontend-workstream.md").exists():
        errors.append("frontend-workstream.md must exist when frontend_required is true.")
    if not frontend_required and (artifacts_dir / "frontend-workstream.md").exists():
        errors.append("frontend-workstream.md must not exist when frontend_required is false.")
    if backend_required and not (artifacts_dir / "backend-workstream.md").exists():
        errors.append("backend-workstream.md must exist when backend_required is true.")
    if not backend_required and (artifacts_dir / "backend-workstream.md").exists():
        errors.append("backend-workstream.md must not exist when backend_required is false.")
    if migration_required and not (artifacts_dir / "migration-cutover-plan.md").exists():
        errors.append("migration-cutover-plan.md must exist when migration_required is true.")
    if not migration_required and (artifacts_dir / "migration-cutover-plan.md").exists():
        errors.append("migration-cutover-plan.md must not exist when migration_required is false.")

    if str(upstream_refs.get("feat_ref") or "") != str(bundle_json.get("feat_ref") or ""):
        errors.append("upstream-design-refs.json feat_ref must match impl-bundle.json.")
    if str(upstream_refs.get("tech_ref") or "") != str(bundle_json.get("tech_ref") or ""):
        errors.append("upstream-design-refs.json tech_ref must match impl-bundle.json.")

    if handoff.get("target_template_id") != DOWNSTREAM_TEMPLATE_ID:
        errors.append(f"handoff-to-feature-delivery.json must target {DOWNSTREAM_TEMPLATE_ID}.")
    if handoff.get("target_template_path") != DOWNSTREAM_TEMPLATE_PATH:
        errors.append("handoff-to-feature-delivery.json target_template_path is incorrect.")
    for field in ["feat_ref", "impl_ref", "tech_ref"]:
        if str(handoff.get(field) or "") != str(bundle_json.get(field) or ""):
            errors.append(f"handoff-to-feature-delivery.json {field} must match impl-bundle.json.")

    manifest_status = str(manifest.get("status") or "")
    bundle_status = str(bundle_json.get("status") or "")
    smoke_status = str(smoke_gate.get("status") or "")
    if manifest_status not in {"in_progress", "execution_ready", "blocked"}:
        errors.append("package-manifest.json.status is invalid.")
    if bundle_status not in {"in_progress", "execution_ready", "blocked"}:
        errors.append("impl-bundle.json.status is invalid.")
    if smoke_status not in {"pending_review", "pending_execution", "blocked"}:
        errors.append("smoke-gate-subject.json.status is invalid.")
    if manifest_status != bundle_status:
        errors.append("package-manifest.json.status must match impl-bundle.json.status.")
    if bundle_status == "execution_ready" and (smoke_status != "pending_execution" or smoke_gate.get("ready_for_execution") is not True):
        errors.append("execution_ready packages must have ready_for_execution true and pending_execution smoke status.")
    if bundle_status == "blocked" and smoke_status != "blocked":
        errors.append("blocked packages must have blocked smoke gate subject.")
    if bundle_status == "in_progress" and smoke_gate.get("ready_for_execution") is True:
        errors.append("in_progress packages must not already be ready_for_execution.")

    return errors, {
        "valid": not errors,
        "feat_ref": bundle_json.get("feat_ref"),
        "tech_ref": bundle_json.get("tech_ref"),
        "impl_ref": bundle_json.get("impl_ref"),
        "manifest_status": manifest_status,
        "smoke_gate_status": smoke_status,
    }


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors

    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    review_report = load_json(artifacts_dir / "impl-review-report.json")
    acceptance_report = load_json(artifacts_dir / "impl-acceptance-report.json")
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")

    readiness_errors: list[str] = []
    if bundle_json.get("status") != "execution_ready":
        readiness_errors.append("impl-bundle.json status must be execution_ready.")
    if manifest.get("status") != "execution_ready":
        readiness_errors.append("package-manifest.json status must be execution_ready.")
    if review_report.get("decision") != "pass":
        readiness_errors.append("impl-review-report.json decision must be pass.")
    if acceptance_report.get("decision") != "approve":
        readiness_errors.append("impl-acceptance-report.json decision must be approve.")
    if smoke_gate.get("ready_for_execution") is not True:
        readiness_errors.append("smoke-gate-subject.json must mark ready_for_execution true.")
    return not readiness_errors, readiness_errors


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-dev-tech-to-impl Evidence Report",
                "",
                "## Run Summary",
                "",
                f"- run_id: {execution.get('run_id')}",
                f"- inputs: {', '.join(str(item) for item in execution.get('inputs', []))}",
                f"- output_dir: {artifacts_dir}",
                "",
                "## Execution Evidence",
                "",
                f"- commands: {', '.join(execution.get('commands_run', []))}",
                f"- decisions: {', '.join(execution.get('key_decisions', []))}",
                "",
                "## Supervision Evidence",
                "",
                f"- decision: {supervision.get('decision')}",
                f"- reason: {supervision.get('reason')}",
                "",
                "## Smoke Gate Subject",
                "",
                f"- status: {smoke_gate.get('status')}",
                f"- ready_for_execution: {smoke_gate.get('ready_for_execution')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path

#!/usr/bin/env python3
"""
Lite-native runtime support for tech-to-impl.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tech_to_impl_builder import build_candidate_package
from tech_to_impl_common import guess_repo_root_from_input, load_tech_package, slugify, validate_input_package
from tech_to_impl_review import (
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    validate_output_package,
    validate_package_readiness,
    write_executor_outputs,
)


def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "tech-to-impl" / run_id


def executor_run(input_path: Path, feat_ref: str, tech_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path, feat_ref, tech_ref)
    if errors:
        raise ValueError("; ".join(errors))

    package = load_tech_package(input_path)
    effective_run_id = run_id or f"{package.run_id}--{slugify(tech_ref).lower()}"
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    generated = build_candidate_package(package, effective_run_id)
    write_executor_outputs(
        output_dir,
        package,
        generated,
        f"python scripts/tech_to_impl.py executor-run --input {input_path} --feat-ref {feat_ref} --tech-ref {tech_ref}",
    )
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "impl_ref": generated["bundle_json"]["impl_ref"],
    }


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    del repo_root, run_id, allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

    supervision = build_supervision_evidence(artifacts_dir)
    update_supervisor_outputs(artifacts_dir, supervision)
    from tech_to_impl_common import load_json

    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    return {
        "ok": True,
        "run_id": supervision["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "execution_ready": smoke_gate.get("ready_for_execution") is True,
    }


def run_workflow(input_path: Path, feat_ref: str, tech_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        feat_ref=feat_ref,
        tech_ref=tech_ref,
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    supervisor_result = supervisor_review(artifacts_dir, repo_root, run_id or executor_result["run_id"], allow_update=True)
    output_errors, output_result = validate_output_package(artifacts_dir)
    if output_errors:
        raise ValueError("; ".join(output_errors))
    readiness_ok, readiness_errors = validate_package_readiness(artifacts_dir)
    report_path = collect_evidence_report(artifacts_dir)
    return {
        "ok": readiness_ok,
        "run_id": executor_result["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "impl_ref": executor_result["impl_ref"],
        "supervision": supervisor_result,
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }

#!/usr/bin/env python3
"""
CLI entrypoint for the lite-native tech-to-impl runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tech_to_impl_common import validate_input_package
from tech_to_impl_runtime import (
    collect_evidence_report,
    executor_run,
    repo_root_from,
    run_workflow,
    supervisor_review,
    validate_output_package,
    validate_package_readiness,
)


def command_run(args: argparse.Namespace) -> int:
    result = run_workflow(
        input_path=Path(args.input).resolve(),
        feat_ref=args.feat_ref,
        tech_ref=args.tech_ref,
        repo_root=repo_root_from(args.repo_root, Path(args.input).resolve()),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def command_executor_run(args: argparse.Namespace) -> int:
    result = executor_run(
        input_path=Path(args.input).resolve(),
        feat_ref=args.feat_ref,
        tech_ref=args.tech_ref,
        repo_root=repo_root_from(args.repo_root, Path(args.input).resolve()),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_supervisor_review(args: argparse.Namespace) -> int:
    result = supervisor_review(
        artifacts_dir=Path(args.artifacts_dir).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.artifacts_dir).resolve()),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("execution_ready") else 1


def command_validate_input(args: argparse.Namespace) -> int:
    errors, result = validate_input_package(Path(args.input).resolve(), args.feat_ref, args.tech_ref)
    print(json.dumps({"ok": not errors, "result": result, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def command_validate_output(args: argparse.Namespace) -> int:
    errors, result = validate_output_package(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": not errors, "result": result, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def command_collect_evidence(args: argparse.Namespace) -> int:
    report_path = collect_evidence_report(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": True, "report_path": str(report_path)}, ensure_ascii=False))
    return 0


def command_validate_package_readiness(args: argparse.Namespace) -> int:
    ok, errors = validate_package_readiness(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1


def command_freeze_guard(args: argparse.Namespace) -> int:
    return command_validate_package_readiness(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the tech-to-impl workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--input", required=True)
    run_parser.add_argument("--feat-ref", required=True)
    run_parser.add_argument("--tech-ref", required=True)
    run_parser.add_argument("--repo-root")
    run_parser.add_argument("--run-id")
    run_parser.add_argument("--allow-update", action="store_true")
    run_parser.set_defaults(func=command_run)

    executor_parser = subparsers.add_parser("executor-run")
    executor_parser.add_argument("--input", required=True)
    executor_parser.add_argument("--feat-ref", required=True)
    executor_parser.add_argument("--tech-ref", required=True)
    executor_parser.add_argument("--repo-root")
    executor_parser.add_argument("--run-id")
    executor_parser.add_argument("--allow-update", action="store_true")
    executor_parser.set_defaults(func=command_executor_run)

    supervisor_parser = subparsers.add_parser("supervisor-review")
    supervisor_parser.add_argument("--artifacts-dir", required=True)
    supervisor_parser.add_argument("--repo-root")
    supervisor_parser.add_argument("--run-id")
    supervisor_parser.add_argument("--allow-update", action="store_true")
    supervisor_parser.set_defaults(func=command_supervisor_review)

    validate_input_parser = subparsers.add_parser("validate-input")
    validate_input_parser.add_argument("--input", required=True)
    validate_input_parser.add_argument("--feat-ref", required=True)
    validate_input_parser.add_argument("--tech-ref", required=True)
    validate_input_parser.set_defaults(func=command_validate_input)

    validate_output_parser = subparsers.add_parser("validate-output")
    validate_output_parser.add_argument("--artifacts-dir", required=True)
    validate_output_parser.set_defaults(func=command_validate_output)

    collect_parser = subparsers.add_parser("collect-evidence")
    collect_parser.add_argument("--artifacts-dir", required=True)
    collect_parser.set_defaults(func=command_collect_evidence)

    readiness_parser = subparsers.add_parser("validate-package-readiness")
    readiness_parser.add_argument("--artifacts-dir", required=True)
    readiness_parser.set_defaults(func=command_validate_package_readiness)

    freeze_parser = subparsers.add_parser("freeze-guard")
    freeze_parser.add_argument("--artifacts-dir", required=True)
    freeze_parser.set_defaults(func=command_freeze_guard)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py validate-input --input "$1" --feat-ref "$2" --tech-ref "$3"

#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py validate-output --artifacts-dir "$1"

