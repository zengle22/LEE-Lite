---
name: ll-qa-api-spec-to-tests
description: Converts frozen api-test-spec YAML into executable pytest test scripts with embedded evidence collection per ADR-047 Section 6.3.
---

# LL QA API Spec-to-Tests Generation

This skill implements the ADR-047 generation layer for API tests. It accepts frozen `api-test-spec` YAML files and generates executable pytest test scripts with embedded evidence collection hooks.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Upstream handoff: `ll-qa-api-spec-gen` (api-test-spec YAML files)
- Downstream consumer: `ll-qa-api-test-exec` (generated pytest scripts)

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `Frozen Spec -> Executable Test Scripts` derivation.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one or more frozen `api-test-spec` YAML files from `ssot/tests/api/{feat_id}/api-test-spec/`.
2. Validate each spec using `qa_schemas --type spec` — must contain `api_test_spec` root key with `case_id`, `coverage_id`, `endpoint`, `capability`, `expected` sections.
3. For each valid spec, invoke the LLM executor to generate a pytest test script containing:
   - Test class with docstring showing case_id and coverage_id
   - Test method implementing the spec contract (preconditions, request, assertions)
   - Embedded evidence collection code writing YAML per ADR-047 Section 6.3
   - Error handling that writes evidence on failure
4. Write generated scripts to `ssot/tests/api/{feat_id}/tests/`.
5. Run supervisor agent to validate each generated script (syntax, evidence hooks, structure).
6. Emit generated `.py` files to output directory.

## Workflow Boundary

- Input: one or more frozen `api-test-spec` YAML files
- Output: executable pytest `.py` test scripts with evidence collection
- Out of scope: running the tests (downstream `ll-qa-api-test-exec`), updating manifest (downstream)

## Non-Negotiable Rules

- Spec files are frozen contracts — generated scripts MUST NOT modify them.
- Every generated test script MUST write evidence YAML during execution.
- Evidence YAML output path MUST include run_id for collision avoidance.
- Generated scripts must handle errors gracefully: on exception, write evidence with `execution_status: "error"`.
- Every `evidence_required` item from the spec must have corresponding evidence-writing code.
