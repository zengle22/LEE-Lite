# Phase 17: 双链统一入口 + spec 桥接跑通 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-24
**Phase:** 17-chain-entrypoint
**Areas discussed:** Orchestrator mechanism, StepResult location, Concurrency control, --resume persistence

---

## Area 1: Orchestrator mechanism (ENTRY-01/02)

| Option | Description | Selected |
|--------|-------------|----------|
| AI agent orchestrator via Skill tool /ll-xxx calls | AI agent (agents/orchestrator.md) sequences sub-skills via Skill tool. Each sub-skill is independent and individually invokable. | ✓ |
| CLI runtime script | A Python script orchestrating sub-skills via qa_skill_runtime.run_skill() or subprocess. Adds a new CLI layer. | |
| Hook chain | After each skill completes, a hook triggers the next skill automatically. Requires runtime changes to qa_skill_runtime.py. | |

**User's choice:** AI agent orchestrator via Skill tool /ll-xxx calls
**Notes:** User confirmed understanding that ll-qa-api-from-feat is a Claude Code Skill (AI agent), NOT a CLI script. The orchestrator sequences sub-skills via Skill tool calls. test_orchestrator.py is a separate CLI module for actual test execution.

---

## Area 2: StepResult dataclass location (BRIDGE-06)

| Option | Description | Selected |
|--------|-------------|----------|
| cli/lib/contracts.py (new file) | Shared DTOs for cross-cutting data structures. StepResult here, future contracts here. Clean separation. | ✓ |
| cli/lib/test_orchestrator.py | Co-located with orchestrator that produces/consumes it. No new file. | |
| cli/lib/test_exec_runtime.py | Near execute_test_exec_skill() which produces StepResult. Couples to one producer. | |

**User's choice:** cli/lib/contracts.py (new file)
**Notes:** StepResult is purely a CLI concern (test_orchestrator.py Step 3 → Step 4 data contract), not AI agent domain.

---

## Area 3: Manifest concurrency control (BRIDGE-07)

| Option | Description | Selected |
|--------|-------------|----------|
| Timestamp + version optimistic lock | Read manifest._version, update with new version. If version changed since read, retry. Windows-compatible, no file locking issues. | ✓ (Claude's discretion) |
| fcntl.flock (POSIX only) | Standard file locking. Does NOT work on Windows (fcntl maps to nothing). | |

**User's choice:** You decide
**Claude's discretion:** Timestamp + version optimistic lock — Windows compatible, avoids POSIX-only fcntl issues

---

## Area 4: --resume persistence mechanism (BRIDGE-08)

| Option | Description | Selected |
|--------|-------------|----------|
| Run manifest per execution (Phase 18) | run_manifest_gen.py writes execution record. --resume reads latest run manifest. Clean separation of concerns. | ✓ |
| Inline in coverage manifest | api-coverage-manifest.yaml gets last_run_status field per item. --resume reads that directly. Simpler but mixes execution state into design artifact. | |
| Separate .resume state file per feat | ssot/tests/.resume/{feat_id}.json stores failed coverage_ids. Simple key-value. One more file to track. | |

**User's choice:** Run manifest per execution (Recommended)
**Notes:** CRITICAL ISSUE: run_manifest_gen.py is Phase 18 (EXEC-01). Phase 17 ll-qa-test-run needs --resume NOW.

**Resolution — Phase 17 fallback:**

| Option | Description | Selected |
|--------|-------------|----------|
| Manifest inline as Phase 17 fallback | Phase 17: --resume reads/writes lifecycle_status directly in coverage manifest. Phase 18: migrate to run_manifest. Clean handoff. | ✓ |
| Separate .resume state file in Phase 17 | Phase 17: use ssot/tests/.resume/{feat_id}.json. Phase 18: migrate to run_manifest. Same migration path. | |
| Defer --resume to Phase 18 | Skip --resume implementation in Phase 17 (BRIDGE-08 not implemented until Phase 18). Faster Phase 17 delivery. | |

**User's choice:** Manifest inline as Phase 17 fallback
**Notes:** Phase 17 --resume works via manifest inline. Phase 18 migrates to run_manifest_gen.py with no breaking changes.

---

## Claude's Discretion

The following were left to planner's judgment:
- Specific orchestrator prompt wording and error handling nuances
- SPEC_ADAPTER_COMPAT YAML field naming (follow ADR-054 §2.2 mapping rules)
- spec_adapter.py internal implementation structure
- environment_provision.py specific implementation details

---

## Deferred Ideas

None — all discussion stayed within phase scope.
