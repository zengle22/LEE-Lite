---
name: ll-test-exec-web-e2e
description: Governed QA execution skill for routing a formal TESTSET plus TestEnvironmentSpec into the canonical Playwright-backed web E2E runtime, then returning a governed response envelope with execution artifacts, candidate registration, and gate handoff refs.
---

# Test Exec Web E2E

This is the formal governed skill wrapper for the ADR-007 web execution path. It does not create a second implementation. It routes into the canonical workspace runtime at `python -m cli.ll skill test-exec-web-e2e`.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-007-QA Test Execution Governed Skill 标准方案.MD`
- Upstream producer: `ll-qa-feat-to-testset`
- Canonical runtime command: `python -m cli.ll skill test-exec-web-e2e --request <request.json> --response-out <response.json>`
- Canonical runtime carrier: `E:\ai\LEE-Lite-skill-first\cli\lib\test_exec_runtime.py`
- Web translator and runner: `E:\ai\LEE-Lite-skill-first\cli\lib\test_exec_playwright.py`

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
3. Require `payload.test_set_ref` to resolve to a formal `TESTSET` and `payload.test_environment_ref` to resolve to a `TestEnvironmentSpec` with `execution_modality: web_e2e`.
4. Preserve optional UI binding sources when provided through `frontend_code_ref`, `ui_runtime_ref`, or `ui_source_spec`.
5. Run the canonical runtime command and let the workspace runtime derive `resolved_ssot_context`, `ui_intent`, `ui_source_context`, `ui_binding_map`, `TestCasePack`, `ScriptPack`, `EvidenceBundle`, `TSE`, and governed candidate refs.
6. Validate the response envelope structurally, then review the semantic boundary: run status, handoff presence, candidate refs, and execution artifact completeness.
7. Freeze only after the response envelope is structurally valid, semantically reviewable, and not in `run_status=failed`.

## Workflow Boundary

- Input: one governed request envelope that references a formal `TESTSET`, one `TestEnvironmentSpec`, and optional UI source refs.
- Output: one governed response envelope for `skill.test-exec-web-e2e`; `response.data` contains candidate refs, handoff refs, and all execution artifact refs.
- Downstream handoff: mainline gate queue via the runtime-produced `handoff_ref`.
- Out of scope: self-approving the gate decision, mutating the source `TESTSET`, or fabricating locator bindings when no authoritative UI source exists.

## Non-Negotiable Rules

- Do not bypass `python -m cli.ll skill test-exec-web-e2e` with hand-written response files.
- Do not treat governance text alone as sufficient for executable locators; unresolved bindings must remain `partial` or `fallback_smoke`.
- Do not rewrite `run_status` or artifact refs after execution to make a run look healthier.
- Do not let executor logic issue acceptance or closure decisions; gate consumers own those states.
