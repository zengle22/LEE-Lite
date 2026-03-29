---
id: SRC-005
ssot_type: SRC
title: ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 修订版
status: frozen
version: v1
schema_version: 1.0.0
src_root_id: src-root-src-005
workflow_key: product.raw-to-src
workflow_run_id: adr011-raw2src-fix-20260327-r1
source_kind: governance_bridge_src
source_refs:
- ADR-011
- ADR-001
- ADR-003
- ADR-004
- ADR-005
- ADR-006
- ADR-008
- ADR-009
candidate_package_ref: artifacts/raw-to-src/adr011-raw2src-fix-20260327-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-27T13:25:38Z'
---

# ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 修订版

## 问题陈述

当前已落地的治理语义仍分散在 skill、runtime、contract 与测试中；如果不把这些约束收敛成统一的 SRC 继承源，下游会继续各自重写输入边界、冻结条件与交接规则。

## 目标用户

- 受该治理规则约束的 skill 作者
- workflow / orchestration 设计者
- human gate / reviewer
- artifact 管理与治理消费者

## 触发场景

- 当治理类变更需要被下游 skill 继承时。

## 业务动因

- 需要现在就把这类治理变化收敛成正式需求源，否则下游消费、审计和交付对象持续不稳定会继续沿后续需求链扩散。
- 将 ADR 归一为 bridge SRC 的价值，是让下游围绕 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 共享同一组继承约束，而不是继续各自猜路径或重写规则。
- 这能为后续链路提供稳定输入：下游需求链必须将 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## 语义清单

- Actors: 受该治理规则约束的 skill 作者; workflow / orchestration 设计者; human gate / reviewer; artifact 管理与治理消费者
- Product surfaces: ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 对应的正式对象、contract 或 policy; skill author 不再自行定义等价治理对象或边界。; reviewer 可在不回读原始 ADR 的前提下判断候选是否满足主要约束。; 下游消费方可按统一 contract、boundary 与 lineage 读取正式对象。
- Operator surfaces: ll artifact commit
- Entry points: ll artifact commit
- Commands: ll artifact commit
- Runtime objects: None
- States: * 如果只读 `SKILL.md`，会漏掉结构化字段、缺陷策略、CLI commit 与 freeze-ready 条件；; 2. 它的唯一正式输入是 **freeze-ready 的 `epic_freeze_package`**，且必须来自 `product.src-to-epic`。; * `epic-freeze-gate.json.freeze_ready = true`; * 未 freeze-ready 的 EPIC candidate; * 在当前实现中给出 `pass / revise` 结论，并据此决定 freeze-ready 与否; freeze-ready EPIC package; 若 `rollout_required = true` 却没有生成 `skill-adoption-e2e` FEAT，当前实现会记为 `P1` 缺陷，并阻断 freeze-ready。; freeze-ready 需同时满足：
- Observability surfaces: None

## 标准化决策

- source_projection: 将原始输入统一映射为主链兼容的标准字段。 (loss_risk=low)
- bridge_projection: 为下游 workflow 提供兼容的 bridge projection，同时保留 high-fidelity source layer。 (loss_risk=medium)
- operator_surface_preservation: 避免 CLI/operator/control surface 在 SRC 层被静默压缩。 (loss_risk=low)

## 压缩与省略说明

- Compressed: problem_statement | why=正文会被整理为适合下游消费的规范化问题陈述。 | risk=low
- Compressed: bridge_context | why=bridge projection 会把 raw 中分散的治理语义压缩为统一继承视图。 | risk=medium
- Summary: SRC 同时保留 high-fidelity source layer 和 bridge projection；任何压缩都必须显式记录。

## Operator Surface Inventory

- cli_control_surface: ll artifact commit | phase=run | actor=Claude/Codex CLI operator

## 用户入口与控制面

- CLI control surface: ll artifact commit
- 用户交互边界: 用户通过 Claude/Codex CLI 显式调用 skill 入口或控制命令启动、恢复、观察运行时。

## 冲突与未决点

- No explicit contradictions detected during normalization.

## 目标能力对象

- ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 对应的正式对象、contract 或 policy

## 成功结果

- skill author 不再自行定义等价治理对象或边界。
- reviewer 可在不回读原始 ADR 的前提下判断候选是否满足主要约束。
- 下游消费方可按统一 contract、boundary 与 lineage 读取正式对象。

## 治理变更摘要

- 治理对象：ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界
- 统一原则：正式文件读写统一纳入围绕 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 的治理边界，不再依赖分散约定。
- 下游必须继承的约束：下游需求链必须将 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## 下游派生要求

- 围绕治理对象定义正式 contract、schema、policy 与 lifecycle。
- 把关键约束落成可校验的 validation、evidence 与 gate-ready 输出。
- 确保下游 EPIC / FEAT / TASK 不遗漏主要治理对象与继承边界。

## 关键约束

- 正式文件读写必须围绕 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 的统一边界建模，不得在下游恢复自由路径写入。
- 下游需求链必须将 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## 范围边界

- In scope: 定义 skill 文件读写、artifact 输入输出边界与路径策略的统一治理边界。
- In scope: 为后续主链对象提供统一约束来源与交接依据，而不是在本层展开 API 或实现设计。
- Out of scope: 下游 EPIC/FEAT/TASK 分解与实现细节。

## 来源追溯

- Source refs: ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
- Input type: adr

## 桥接摘要

- 本 SRC 的作用不是重复 ADR 论证，而是把治理结论转译成下游可直接继承的正式边界。
- 下游应默认继承这里定义的治理对象、约束和交接边界，而不是重新发明等价规则。

## Bridge Context

- 结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。
- governed_by_adrs: ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
- change_scope: 将《ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线》涉及的ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界收敛为统一主链继承边界，明确 loop、handoff、gate 与 formal materialization 的协作责任。
- governance_objects: ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界
- current_failure_modes: 如果不补这层文档，后续最容易发生三类漂移：; 下游在 TECH / TESTSET / IMPL 主链消费时，各自重新解释输入、边界、freeze 条件与 traceability。; *epic-to-feat 不是“从任何上游说明文档继续拆 FEAT”，而是“只消费已通过上游治理的 EPIC freeze package”。**
- downstream_inheritance_requirements: 下游需求链必须将 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。
- expected_downstream_objects: EPIC, FEAT, TASK
- acceptance_impact: 下游 gate、auditor 与 handoff 必须基于同一组受治理边界判断正式产物是否合法。; 下游消费方应能在不回读原始 ADR 的前提下理解主要失控行为与统一治理理由。; 审计链应能回答谁推进了 candidate、谁做了 final decision、为什么允许推进、正式物化了什么对象。
- non_goals: 下游 EPIC/FEAT/TASK 分解与实现细节。
