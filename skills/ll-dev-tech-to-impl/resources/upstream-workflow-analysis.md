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

