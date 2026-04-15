---
phase: "05"
plan: 05
type: execute
completed: "2026-04-15"
tasks_completed: 3
tasks_total: 3
commits:
  - hash: d851a9e
    message: "create ll-qa-e2e-test-exec execution skill skeleton (14 files)"
  - hash: e9dd53d
    message: "create e2e_test_exec.py with Playwright execution logic"
  - hash: 3bd2672
    message: "register 4 new CLI actions in _QA_SKILL_MAP and ll.py"
---

# Phase 05 Plan 05: E2E Test Execution Skill + CLI Registration Summary

**One-liner:** E2E Playwright test execution skill with code-driven run.sh, Python execution module, and 4 new CLI action registrations for spec-to-tests generation and test execution dispatch.

## Key Files

### Created
- `skills/ll-qa-e2e-test-exec/SKILL.md` — E2E execution skill description (code-driven)
- `skills/ll-qa-e2e-test-exec/ll.lifecycle.yaml` — Lifecycle states (draft/validated/executed/frozen)
- `skills/ll-qa-e2e-test-exec/ll.contract.yaml` — Skill metadata (adr: ADR-047, category: execution, chain: e2e)
- `skills/ll-qa-e2e-test-exec/input/contract.yaml` — Input contract (spec_path, test_dir, manifest_path, etc.)
- `skills/ll-qa-e2e-test-exec/input/semantic-checklist.md` — Input validation checklist
- `skills/ll-qa-e2e-test-exec/output/contract.yaml` — Output contract (evidence_dir, manifest_updated, results)
- `skills/ll-qa-e2e-test-exec/output/semantic-checklist.md` — Output validation checklist
- `skills/ll-qa-e2e-test-exec/scripts/run.sh` — Code-driven entry: ensures Playwright installed, invokes e2e_test_exec.py
- `skills/ll-qa-e2e-test-exec/scripts/validate_input.sh` — Validates .spec.ts files, e2e spec, manifest
- `skills/ll-qa-e2e-test-exec/scripts/validate_output.sh` — Validates evidence YAML files pass schema
- `skills/ll-qa-e2e-test-exec/evidence/execution-evidence.schema.json` — Execution evidence schema
- `skills/ll-qa-e2e-test-exec/evidence/supervision-evidence.schema.json` — Supervision evidence schema
- `skills/ll-qa-e2e-test-exec/agents/executor.md` — Supervisory executor prompt (minimal)
- `skills/ll-qa-e2e-test-exec/agents/supervisor.md` — Post-execution validation checklist
- `cli/lib/e2e_test_exec.py` — Core E2E execution: runs Playwright, parses JSON report, validates evidence, backfills manifest

### Modified
- `cli/commands/skill/command.py` — Added 4 entries to _QA_SKILL_MAP, 4 to ensure() set, EXEC_SKILL_RUNTIME dispatch block
- `cli/ll.py` — Added 4 actions to skill subparser tuple

## Deviations from Plan

None — plan executed exactly as written.

## Threat Surface Scan

| Threat ID | Category | Component | Mitigation |
|-----------|----------|-----------|------------|
| T-05-14 | Tampering | Playwright installation | run.sh checks node_modules/@playwright/test exists before npm install; pins @playwright/test@^1.58.2 |
| T-05-15 | Repudiation | E2E evidence validation | validate_evidence() called for each evidence file; all spec.evidence_required items checked |
| T-05-16 | Tampering | Manifest backfill | backfill_manifest() uses atomic write (temp file + os.replace) |
| T-05-17 | Injection | Environment variables | Only EVIDENCE_DIR, EVIDENCE_RUN_ID, TARGET_URL passed to subprocess |
| T-05-18 | Injection | CLI action dispatch | ensure() validates ctx.action against known set; EXEC_SKILL_RUNTIME uses import_module with explicit module paths |

## Metrics

| Metric | Value |
|--------|-------|
| Files created | 15 |
| Files modified | 2 |
| Total lines added | ~720 |
| Tasks completed | 3/3 |
| Duration | < 5 minutes |

## Self-Check: PASSED

- All 14 skill files verified at skills/ll-qa-e2e-test-exec/
- e2e_test_exec.py import verified
- command.py import verified
- All acceptance criteria grep checks passed
- All 3 commits present in git log
