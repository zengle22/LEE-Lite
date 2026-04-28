# Milestones

## v2.2.1 Failure Case Resolution (In Progress: Started 2026-04-27)

**Status:** IN_PROGRESS

**Goal:** 修复 `tests/defect/failure-cases/` 目录下记录的所有缺陷，同时系统性改进相关技能的质量和稳健性

**Phases planned:** 5 phases (20-24)

**Key fixes planned:**
- P0: SRC003 SSOT 多维度漂移、FEAT 分解按 UI 表面问题
- P1: PROTO 低保真、TECH/IMPL 漂移、TESTSET 模板问题、impl-spec-test 中文解析
- ENH: 多个技能质量增强（api_required、ssot_type、source_refs、API设计、自动触发）

---

## v2.2 双链执行闭环 (Shipped: 2026-04-24)

**Phases completed:** 3 phases (17-19), 11 plans, 487 tests

**Key accomplishments:**
- 需求轴统一入口：ll-qa-api-from-feat, ll-qa-e2e-from-proto
- spec 桥接层：SPEC_ADAPTER_COMPAT, spec_adapter.py, test_orchestrator.py
- 环境管理层：environment_provision.py, ssot/environments/
- 实施轴 P0 模块：run_manifest_gen.py, scenario_spec_compile.py, state_machine_executor.py
- 验收闭环：independent_verifier.py, settlement_integration.py, gate_integration.py
- 487 个测试全部通过

---

## v2.1 双链双轴测试强化 (Shipped: 2026-04-23)

**Phases completed:** 4 phases (13-16), ~10 plans

**Key accomplishments:**
- TESTSET/Environment/Gate YAML Schema 定义
- enum_guard.py + governance_validator.py
- Frozen Contract 追溯（FC-001~FC-007）
- SSOT 写入路径集成

---

## v2.0 ADR-050/051 SSOT 语义治理升级 (Shipped: 2026-04-22)

**Phases completed:** ~5 phases

**Key accomplishments:**
- FRZ 冻结层结构 + MSC 5维验证
- SSOT 语义抽取链
- 变更分级机制

---

## v1.1 ADR-049 体验修正层 (Shipped: 2026-04-21)

**Phases completed:** ~3 phases

**Key accomplishments:**
- ll-patch-capture skill with dual-path execution
- Patch-aware context resolver + AI Context Injection
- PreToolUse Hook 集成

---

## v1.0 ADR-047 双链测试 (Shipped: 2026-04-17)

**Phases completed:** 4 phases, 8 plans, 24 tasks

**Key accomplishments:**

- ADR-049 governed ll-patch-capture skill skeleton with dual-path execution protocol, 6-state lifecycle, and input/output contracts
- Commit:
- Prompt-first runtime infrastructure for ll-qa-gate-evaluate skill: 3 shell scripts, lifecycle config, and evidence JSON schema
- Backward compatibility skill aggregating dual-chain plan/manifest/spec/settlement artifacts into legacy testset-compatible JSON view
- Registered 3 new QA skill actions in CLI handler, added gate output validator, and deprecated 2 legacy ADR-035 skills
- Patch schema guardrails with reviewed_at, test_impact enforcement, and ManifestItem patch tracking
- PatchContext dataclass + resolve_patch_context() + _check_patch_test_impact() gate, wired into test execution flow
- Patch-aware execution loop: per-item TEST_BLOCKED skip via _patch_blocked flag, TOCTOU re-verification with PATCH_CONTEXT_CHANGED gate, and manifest item marking with acceptance ref preservation

---
