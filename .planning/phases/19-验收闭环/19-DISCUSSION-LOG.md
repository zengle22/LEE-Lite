# Phase 19: 验收闭环 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-24
**Phase:** 19-验收闭环
**Areas discussed:** Verdict Strategy, Main/Non-core Flow Distinction, Confidence Calculation, Integration Strategy, Unit Test Scope

---

## Verdict Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| 基于覆盖率 | 执行覆盖率 ≥ 80% → pass；60-80% → conditional_pass；< 60% → fail | |
| 基于失败数量 | 失败用例 < 5% → pass；5-20% → conditional_pass；> 20% → fail | |
| 基于置信度阈值 | 置信度 ≥ 90% → pass；70-90% → conditional_pass；< 70% → fail | |
| 阶梯式复合 | 覆盖率 + 失败率 + 置信度三者加权 | |
| **分层判定（用户自定义）** | 主流程：覆盖率100%（可灵活）、失败容忍0；非核心流程：覆盖率80%（可灵活）、失败容忍3-5个 | ✓ |

**User's choice:** 分层判定策略 — 主流程必须100%覆盖+0失败，非核心流程80%覆盖+3-5失败容忍，置信度作为参考指标
**Notes:** 是否通过应该是一个更加科学的判断，覆盖率是基础，主流程必须全覆盖，非核心流程覆盖率80%（可灵活）；失败数据，主流程1个就不通过，非核心流程容忍3-5个（可灵活），置信度作为参考指标列出

---

## Main/Non-core Flow Distinction

| Option | Description | Selected |
|--------|-------------|----------|
| 从 scenario spec 的 scenario_type 推断 | main = scenario_type:main；exception/branch = scenario_type:exception；retry/state = scenario_type:retry/state；默认非核心 | ✓ |
| 从 manifest 的 priority 字段判断 | P0 = 主流程；P1/P2 = 非核心 | |
| 从 acceptance criteria 的 is_critical 标记 | acceptance 有 is_critical 字段标记 | |
| 手动配置 + feature 关联 | 在 independent_verifier 配置文件中指定主流程列表 | |

**User's choice:** 从 scenario spec 的 scenario_type 推断
**Notes:** 已有 scenario_type 字段，直接复用

---

## Confidence Calculation

| Option | Description | Selected |
|--------|-------------|----------|
| 覆盖率 × (1 - 失败率) | confidence = coverage_rate × (1 - failure_rate)。覆盖高+失败少 → 高置信度 | |
| **基于 evidence 完整性** | 有 evidence_refs 的用例占比 | ✓ |
| 基于断言密度 | 平均每个用例的断言数量 | |
| 组合因子 | 覆盖率 + evidence完整性 + 断言密度 三者加权平均 | |

**User's choice:** 基于 evidence 完整性
**Notes:** 置信度 = 有 evidence_refs 的用例占比

---

## Integration Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| **verdict → settlement → gate (推荐)** | independent_verifier → verdict → settlement report → ll-qa-gate-evaluate → final_decision。链式传递 | ✓ |
| verdict + gate 独立决策 | independent_verifier.verdict 和 ll-qa-gate-evaluate.final_decision 独立产出 | |
| verdict 替换 gate-decision | independent_verifier.verdict 直接作为最终判定，不需要 ll-qa-gate-evaluate | |
| 全部合并到 settlement | settlement report 包含 verdict + confidence + final_decision 一体化输出 | |

**User's choice:** verdict → settlement → gate (推荐)
**Notes:** 链式传递，保持各层职责清晰

---

## Unit Test Scope

| Option | Description | Selected |
|--------|-------------|----------|
| spec_adapter + environment_provision + StepResult | 只测试 Phase 17/18 交付的3个核心模块 | |
| + settlement + gate-evaluate | 包含 ll-qa-settlement 和 ll-qa-gate-evaluate 的单元测试 | |
| + independent_verifier | 包含 independent_verifier.py 的单元测试 | |
| **全部** | 覆盖所有相关模块：spec_adapter + env_provision + StepResult + settlement + gate + verifier | ✓ |

**User's choice:** 全部
**Notes:** 覆盖所有相关模块，确保验收闭环的完整测试覆盖

---

## Claude's Discretion

- confidence 的灵活阈值（具体百分比）
- failure_tolerance 的精确容忍数量（3-5 之间选哪个）
- verdict 灵活性配置的具体值

---

## Deferred Ideas

None
