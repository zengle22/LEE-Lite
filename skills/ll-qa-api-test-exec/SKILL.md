---
name: ll-qa-api-test-exec
description: Executes generated pytest scripts, collects evidence YAML, validates evidence completeness, backfills coverage manifest. Code-driven (not Prompt-first).
---

# LL QA API Test Execution

This skill implements the ADR-047 execution layer for API tests. It is **code-driven** (not Prompt-first): unlike Phase 2 skills that delegate to LLM, this skill invokes pytest via subprocess, parses junitxml results, validates evidence files, and updates the coverage manifest atomically.

## Canonical Authority

- ADR: `ssot/adr/ADR-047-双链测试架构与防偷懒治理框架.MD`
- Upstream handoff: `ll-qa-api-spec-to-tests` (generated pytest scripts)
- Downstream consumer: `ll-qa-api-settlement` (evidence + manifest for settlement report)

## Runtime Boundary Baseline

- Interpret this workflow using `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `Generated Tests -> Evidence + Manifest Update` derivation.
- **CODE-DRIVEN**: Execution is handled by `cli/lib/api_test_exec.py`, not by LLM prompts.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept generated pytest test files, an api-test-spec YAML (for evidence_required validation), and a coverage manifest path.
2. Validate inputs: test .py files exist, spec passes `qa_schemas --type spec`, manifest passes `qa_schemas --type manifest`.
3. Invoke `api_test_exec.run_api_test_exec()` which:
   - Runs pytest on test_dir with --junitxml output
   - Parses junitxml results to get per-case pass/fail/error
   - Validates evidence files against spec.evidence_required
   - Atomically updates manifest via `qa_manifest_backfill.backfill_manifest()`
4. Validate outputs: evidence YAML files exist and pass schema validation.
5. Return execution summary: total, passed, failed, evidence_dir, manifest_updated.

## Workflow Boundary

- Input: generated pytest .py files, api-test-spec YAML, coverage manifest
- Output: evidence YAML files, updated manifest, execution summary JSON
- Out of scope: generating test scripts (upstream `ll-qa-api-spec-to-tests`), settlement reporting (downstream `ll-qa-api-settlement`)

## Non-Negotiable Rules

- This skill is CODE-DRIVEN. The LLM executor does NOT generate or run tests directly.
- All test execution happens through `api_test_exec.py` via subprocess.
- Evidence files are validated against schema before manifest backfill.
- Manifest updates are atomic (temp file + os.replace pattern).
- Specs are frozen contracts — execution reads specs, never modifies them.
