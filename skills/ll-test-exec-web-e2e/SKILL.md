---
name: ll-test-exec-web-e2e
description: Governed QA execution skill for expanding a formal TESTSET into requirement-driven web E2E cases, resolving web-specific UI sources, and returning a governed response envelope with execution artifacts, summary refs, candidate registration, and gate handoff refs.
---

# Test Exec Web E2E

This is the formal governed skill wrapper for the ADR-035 web execution path. It does not create a second implementation. It routes into the canonical workspace runtime at `python -m cli skill test-exec-web-e2e`.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-035-TESTSET 驱动的需求覆盖型 Test Case Expansion 基线.MD`
- Upstream producer: `ll-qa-feat-to-testset`
- Primary path: requirement-driven case expansion from a formal TESTSET
- Canonical runtime command: `python -m cli skill test-exec-web-e2e --request <request.json> --response-out <response.json>`
- Canonical runtime carrier: `E:\ai\LEE-Lite-skill-first\cli\lib\test_exec_runtime.py`
- Web translator and runner: `E:\ai\LEE-Lite-skill-first\cli\lib\test_exec_playwright.py`
- Web-specific UI source adapters: `frontend_code_ref`, `ui_runtime_ref`, `ui_source_spec`

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Execution Protocol

1. Accept one structured `test_exec_skill_request` envelope for `skill.test-exec-web-e2e`.
2. Validate the request envelope, payload boundary, and modality-specific input requirements before execution.
3. Require `payload.test_set_ref` to resolve to a formal `TESTSET` that already encodes requirement coverage intent through `functional_areas`, `logic_dimensions`, `state_model`, `coverage_matrix`, and traceable `test_units`.
4. Require `payload.test_environment_ref` to resolve to a `TestEnvironmentSpec` with `execution_modality: web_e2e`.
5. Preserve optional UI binding sources when provided through `frontend_code_ref`, `ui_runtime_ref`, or `ui_source_spec`.
6. Run the canonical runtime command and let the workspace runtime derive `resolved_ssot_context`, `ui_intent`, `ui_source_context`, `ui_binding_map`, `ui_flow_plan`, `TestCasePack`, `ScriptPack`, `EvidenceBundle`, `results_summary`, `coverage_summary`, `coverage_details`, `coverage_report`, `TSE`, and governed candidate refs.
7. Validate the response envelope structurally, then review the semantic boundary: run status, handoff presence, candidate refs, summary refs, and execution artifact completeness.
8. Freeze only after the response envelope is structurally valid, semantically reviewable, and not in `run_status=failed`.

## Workflow Boundary

- Input: one governed request envelope that references a formal `TESTSET`, one `TestEnvironmentSpec`, and optional UI source refs.
- Output: one governed response envelope for `skill.test-exec-web-e2e`; `response.data` contains candidate refs, handoff refs, web-specific UI source refs, summary refs, and all execution artifact refs.
- Downstream handoff: mainline gate queue via the runtime-produced `handoff_ref`.
- Out of scope: self-approving the gate decision, mutating the source `TESTSET`, or fabricating locator bindings when no authoritative UI source exists.

## Non-Negotiable Rules

- Do not bypass `python -m cli skill test-exec-web-e2e` with hand-written response files.
- Do not treat governance text alone as sufficient for executable locators; unresolved bindings must remain `partial` or `fallback_smoke`.
- Do not rewrite `run_status` or artifact refs after execution to make a run look healthier.
- Do not let executor logic issue acceptance or closure decisions; gate consumers own those states.
- Do not demote requirement-driven case expansion back into ad hoc UI-step-only execution.
