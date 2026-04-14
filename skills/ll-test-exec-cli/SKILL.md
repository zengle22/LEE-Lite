---
name: ll-test-exec-cli
description: DEPRECATED -- ADR-035 TESTSET-driven CLI execution skill. Superseded by spec-driven execution (ADR-047). Do not use for new features.
deprecated: true
deprecated_since: "2026-04-14"
superseded_by: "spec-driven execution via ll-qa-api-spec-gen + ll-qa-e2e-spec-gen"
---

> **DEPRECATED**: This skill is superseded by ADR-047 spec-driven execution. New features should use ll-qa-api-spec-gen and ll-qa-e2e-spec-gen which compile tests directly from coverage manifests, not from TESTSET files. This skill is retained for backward compatibility only and will be removed in a future release.

# Test Exec CLI

This is the formal governed skill wrapper for the ADR-035 requirement-driven test expansion path. It does not create a second implementation. It routes into the canonical workspace runtime at `python -m cli skill test-exec-cli`.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-035-TESTSET 驱动的需求覆盖型 Test Case Expansion 基线.MD`
- Upstream producer: `ll-qa-feat-to-testset`
- Canonical runtime command: `python -m cli skill test-exec-cli --request <request.json> --response-out <response.json>`
- Canonical runtime carrier: `E:\ai\LEE-Lite-skill-first\cli\lib\test_exec_runtime.py`
- CLI execution loop: `E:\ai\LEE-Lite-skill-first\cli\lib\test_exec_execution.py`
- Required working directory: repository root `E:\ai\LEE-Lite-skill-first`

## Runtime Boundary Baseline

- Interpret this skill via `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This bundle is a governed `Skill` wrapper for CLI execution. Runtime carrier modules and execution-loop internals remain carriers; they are not separate skill or workflow authorities.

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
5. Distinguish between `smoke/acceptance` runs and `coverage qualification` runs.
   - `smoke/acceptance` runs may set `coverage_enabled: false` and focus on governed flow, candidate registration, and handoff evidence.
   - `coverage qualification` runs may still collect coverage, but they are an enhancement path. The main path is requirement-driven case expansion: start from `TESTSET.functional_areas`, `logic_dimensions`, `state_model`, and `coverage_matrix`, then generate runnable cases that cover functional, boundary, positive, and negative logic.
   - `coverage qualification` may still expand `TestCasePack` revisions when explicit coverage goals are present, but the source `TESTSET` remains the strategy authority.
6. Avoid `python -c` for coverage-enabled paths; prefer a script file such as `tools/run_case.py` or a module entry that coverage can instrument reliably.
7. Run the canonical runtime command from repository root and let the workspace runtime derive `resolved_ssot_context`, `TestCasePack`, `ScriptPack`, `EvidenceBundle`, `TSE`, and governed candidate refs.
8. Treat `TESTSET` as a strategy object, not as a runnable inventory. The runtime may expand `TestCasePack` for qualification, but it must not mutate the source `TESTSET`.
9. Validate the response envelope structurally, then review the semantic boundary: run status, handoff presence, candidate refs, and execution artifact completeness.
10. Freeze only after the response envelope is structurally valid, semantically reviewable, and not in `run_status=failed`.

## Requirement-Driven Expansion Surface

The downstream planning modules in `cli/lib/` are intentionally split so the main runtime can be integrated later without changing the contract:

- `test_exec_traceability.py` derives the functional coverage matrix and traceability rows.
- `test_exec_case_expander.py` turns a formal TESTSET into a traceable `TestCasePack`.
- `test_exec_fixture_planner.py` derives the fixture/state plan for the expanded cases.
- `test_exec_script_mapper.py` binds the cases to executable script templates.

These modules are the stable integration surface for the runtime owner.

## Workflow Boundary

- Input: one governed request envelope that references a formal `TESTSET` and one CLI `TestEnvironmentSpec`.
- Output: one governed response envelope for `skill.test-exec-cli`; `response.data` contains candidate refs, handoff refs, and all execution artifact refs.
- Downstream handoff: mainline gate queue via the runtime-produced `handoff_ref`.
- Out of scope: self-approving the gate decision, mutating the source `TESTSET`, or inventing fake CLI evidence after the run completes.

## Non-Negotiable Rules

- Do not bypass `python -m cli skill test-exec-cli` with hand-written response files.
- Do not mutate command-execution results to turn failures into passes.
- Do not let executor logic issue acceptance or closure decisions; gate consumers own those states.
- Do not push runnable case expansion back into `TESTSET`; expanded cases belong to runtime-generated `TestCasePack` revisions.
- Do not reuse the same `request_id` for a payload that changes meaning; payload changes require a new `request_id` or a new revision identifier.
