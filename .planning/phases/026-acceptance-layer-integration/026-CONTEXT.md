# Phase 26: 验收层集成 (Acceptance Layer Integration)

## Goal
Gate FAIL 后系统自动将 detected bug 提升为 open 真缺陷，gate/settlement 输出契约包含 bug 关联信息，开发者通过 push model 收到修复任务通知。

## Dependencies
- Phase 25: Bug 注册表与状态机 (already implemented: bug_registry.py, bug_phase_generator.py, sync_bugs_to_registry integration)

## Requirements
- GATE-REM-01: Gate Remediation module (gate_remediation.py)
- GATE-REM-02: detected → open auto-promotion
- GATE-INTEG-01: gate-evaluate output contract update
- GATE-INTEG-02: settlement input contract update
- PUSH-MODEL-01: Push model (draft phase, terminal highlight, reminders)

## References
- ADR-055: ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md (§2.4, §2.8A, §3 Phase 2)
- Phase 25 implementation: cli/lib/bug_registry.py, cli/lib/bug_phase_generator.py
- Current contracts: skills/ll-qa-gate-evaluate/, skills/ll-qa-settlement/
- Command integration: cli/commands/skill/command.py

## Key Patterns from Phase 25
- Immutable state machine: transition_bug_status() returns new dict
- Atomic YAML writes: temp file + os.replace()
- Optimistic locking: version field + UUID updates
- on_complete callback pattern: in test_orchestrator.py

## Contract Updates Required
1. gate-evaluate output: add bug_ids map (coverage_id → bug_id)
2. settlement input: accept optional bug registry path for context
3. Both maintain backward compatibility (add fields only, no deletion)
