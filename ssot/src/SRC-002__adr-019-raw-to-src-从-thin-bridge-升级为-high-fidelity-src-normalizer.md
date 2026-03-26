---
id: SRC-002
ssot_type: SRC
title: ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer
status: frozen
version: v1
schema_version: 1.0.0
src_root_id: src-root-src-002
workflow_key: product.raw-to-src
workflow_run_id: adr019-raw-to-src-high-fidelity-src-normalizer-20260326-r2
source_kind: governance_bridge_src
source_refs:
- ADR-019
- ADR-001
- ADR-002
- ADR-003
- ADR-005
- ADR-008
- ADR-010
- ADR-018
candidate_package_ref: artifacts/raw-to-src/adr019-raw-to-src-high-fidelity-src-normalizer-20260326-r2
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T03:13:16Z'
---

# ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer

## 问题陈述

当前仓库中的 raw-to-src 已经成功承担了以下职责： 当前执行链已经出现把输入统一转换为一个可被主链消费的 SRC candidate、让 src-to-epic、epic-to-feat 等下游能够消费稳定字段，而不是直接读取原始文本、src-to-epic 下游当前消费的字段，是否让上游被迫提前压缩，而不是允许下游从完整 SRC 中选择性投影等失控行为。 这会直接造成如果 SRC 层已压缩，下游无法可靠恢复、无法稳定支撑 ADR-018 这类含 operator surface 的需求、新模型的主要成本。 正式文件读写统一纳入围绕 ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 的治理边界，不再依赖分散约定。

## 目标用户

- 受该治理规则约束的 skill 作者
- workflow / orchestration 设计者
- human gate / reviewer
- artifact 管理与治理消费者

## 触发场景

- 当治理类变更需要被下游 skill 继承时。

## 业务动因

- 需要现在就把这类治理变化收敛成正式需求源，否则如果 SRC 层已压缩，下游无法可靠恢复、无法稳定支撑 ADR-018 这类含 operator surface 的需求会继续沿后续需求链扩散。
- 将 ADR 归一为 bridge SRC 的价值，是让下游围绕 ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 共享同一组继承约束，而不是继续各自猜路径或重写规则。
- 这能为后续链路提供稳定输入：下游需求链必须将 ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## 语义清单

- Actors: 受该治理规则约束的 skill 作者; workflow / orchestration 设计者; human gate / reviewer; artifact 管理与治理消费者
- Product surfaces: ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 对应的正式对象、contract 或 policy; skill author 不再自行定义等价治理对象或边界。; reviewer 可在不回读原始 ADR 的前提下判断候选是否满足主要约束。; 下游消费方可按统一 contract、boundary 与 lineage 读取正式对象。
- Operator surfaces: Execution Loop Job Runner; ll loop run-execution; runner observability surface
- Entry points: Execution Loop Job Runner; ll loop run-execution
- Commands: ll loop run-execution
- Runtime objects: None
- States: * gate-ready producer；; * backlog / running / failed / deadletter 等观测面。; * 易于做 gate-ready routing；; 对于 ADR-018 这类输入，如果 `operator_surface_inventory` 缺失，则不得视为高质量 freeze-ready `SRC`。
- Observability surfaces: runner observability surface

## 标准化决策

- source_projection: 将原始输入统一映射为主链兼容的标准字段。 (loss_risk=low)
- bridge_projection: 为下游 workflow 提供兼容的 bridge projection，同时保留 high-fidelity source layer。 (loss_risk=medium)
- operator_surface_preservation: 避免 CLI/operator/control surface 在 SRC 层被静默压缩。 (loss_risk=low)

## 压缩与省略说明

- Compressed: problem_statement | why=正文会被整理为适合下游消费的规范化问题陈述。 | risk=low
- Compressed: bridge_context | why=bridge projection 会把 raw 中分散的治理语义压缩为统一继承视图。 | risk=medium
- Summary: SRC 同时保留 high-fidelity source layer 和 bridge projection；任何压缩都必须显式记录。

## Operator Surface Inventory

- skill_entry: Execution Loop Job Runner | phase=start | actor=workflow / orchestration operator
- cli_control_surface: ll loop run-execution | phase=start | actor=Claude/Codex CLI operator
- monitor_surface: runner observability surface | phase=monitor | actor=workflow / orchestration operator

## 用户入口与控制面

- 主入口 skill: Execution Loop Job Runner
- CLI control surface: ll loop run-execution
- 运行监控面: runner observability surface
- 用户交互边界: 用户通过 Claude/Codex CLI 显式调用 skill 入口或控制命令启动、恢复、观察运行时。

## 冲突与未决点

- No explicit contradictions detected during normalization.

## 目标能力对象

- ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 对应的正式对象、contract 或 policy

## 成功结果

- skill author 不再自行定义等价治理对象或边界。
- reviewer 可在不回读原始 ADR 的前提下判断候选是否满足主要约束。
- 下游消费方可按统一 contract、boundary 与 lineage 读取正式对象。

## 治理变更摘要

- 治理对象：ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界
- 统一原则：正式文件读写统一纳入围绕 ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 的治理边界，不再依赖分散约定。
- 下游必须继承的约束：下游需求链必须将 ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## 下游派生要求

- 围绕治理对象定义正式 contract、schema、policy 与 lifecycle。
- 把关键约束落成可校验的 validation、evidence 与 gate-ready 输出。
- 确保下游 EPIC / FEAT / TASK 不遗漏主要治理对象与继承边界。

## 关键约束

- 正式文件读写必须围绕 ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 的统一边界建模，不得在下游恢复自由路径写入。
- 下游需求链必须将 ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## 范围边界

- In scope: 定义 skill 文件读写、artifact 输入输出边界与路径策略的统一治理边界。
- In scope: 为后续主链对象提供统一约束来源与交接依据，而不是在本层展开 API 或实现设计。
- Out of scope: 下游 EPIC/FEAT/TASK 分解与实现细节。

## 来源追溯

- Source refs: ADR-019, ADR-001, ADR-002, ADR-003, ADR-005, ADR-008, ADR-010, ADR-018
- Input type: adr

## 桥接摘要

- 本 SRC 的作用不是重复 ADR 论证，而是把治理结论转译成下游可直接继承的正式边界。
- 下游应默认继承这里定义的治理对象、约束和交接边界，而不是重新发明等价规则。

## Bridge Context

- 结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。
- governed_by_adrs: ADR-019, ADR-001, ADR-002, ADR-003, ADR-005, ADR-008, ADR-010, ADR-018
- change_scope: 将《ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer》涉及的ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界收敛为统一主链继承边界，明确 loop、handoff、gate 与 formal materialization 的协作责任。
- governance_objects: ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界
- current_failure_modes: 把输入统一转换为一个可被主链消费的 SRC candidate；; 让 src-to-epic、epic-to-feat 等下游能够消费稳定字段，而不是直接读取原始文本。; src-to-epic 下游当前消费的字段，是否让上游被迫提前压缩，而不是允许下游从完整 SRC 中选择性投影；
- downstream_inheritance_requirements: 下游需求链必须将 ADR 019 raw to src 从 Thin Bridge 升级为 High Fidelity SRC Normalizer 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。
- expected_downstream_objects: EPIC, FEAT, TASK
- acceptance_impact: 下游 gate、auditor 与 handoff 必须基于同一组受治理边界判断正式产物是否合法。; 下游消费方应能在不回读原始 ADR 的前提下理解主要失控行为与统一治理理由。; 审计链应能回答谁推进了 candidate、谁做了 final decision、为什么允许推进、正式物化了什么对象。
- non_goals: 下游 EPIC/FEAT/TASK 分解与实现细节。
