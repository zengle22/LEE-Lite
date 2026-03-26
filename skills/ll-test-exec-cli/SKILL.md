---
name: ll-test-exec-cli
description: Governed QA execution skill for routing a formal TESTSET plus TestEnvironmentSpec into the canonical CLI execution runtime, then returning a governed response envelope with execution artifacts, candidate registration, and gate handoff refs.
---

# Test Exec CLI

This is the formal governed skill wrapper for the ADR-007 CLI execution path. It does not create a second implementation. It routes into the canonical workspace runtime at `python -m cli.ll skill test-exec-cli`.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-007-QA Test Execution Governed Skill 标准方案.MD`
- Upstream producer: `ll-qa-feat-to-testset`
- Canonical runtime command: `python -m cli.ll skill test-exec-cli --request <request.json> --response-out <response.json>`
- Canonical runtime carrier: `E:\ai\LEE-Lite-skill-first\cli\lib\test_exec_runtime.py`
- CLI execution loop: `E:\ai\LEE-Lite-skill-first\cli\lib\test_exec_execution.py`

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Execution Protocol

1. Accept one structured `test_exec_skill_request` envelope for `skill.test-exec-cli`.
2. Validate the request envelope, payload boundary, and CLI-specific input requirements before execution.
3. Require `payload.test_set_ref` to resolve to a formal `TESTSET` and `payload.test_environment_ref` to resolve to a `TestEnvironmentSpec` with `execution_modality: cli`.
4. Require the environment contract to expose `command_entry` or `runner_command`.
5. Run the canonical runtime command and let the workspace runtime derive `resolved_ssot_context`, `TestCasePack`, `ScriptPack`, `EvidenceBundle`, `TSE`, and governed candidate refs.
6. Validate the response envelope structurally, then review the semantic boundary: run status, handoff presence, candidate refs, and execution artifact completeness.
7. Freeze only after the response envelope is structurally valid, semantically reviewable, and not in `run_status=failed`.

## Workflow Boundary

- Input: one governed request envelope that references a formal `TESTSET` and one CLI `TestEnvironmentSpec`.
- Output: one governed response envelope for `skill.test-exec-cli`; `response.data` contains candidate refs, handoff refs, and all execution artifact refs.
- Downstream handoff: mainline gate queue via the runtime-produced `handoff_ref`.
- Out of scope: self-approving the gate decision, mutating the source `TESTSET`, or inventing fake CLI evidence after the run completes.

## Non-Negotiable Rules

- Do not bypass `python -m cli.ll skill test-exec-cli` with hand-written response files.
- Do not mutate command-execution results to turn failures into passes.
- Do not let executor logic issue acceptance or closure decisions; gate consumers own those states.
