---
id: SRC-001
ssot_type: SRC
title: ADR 005 Skill 文件读写采用 Artifact IO Gateway + Path Policy 统一治理
status: frozen
version: v1
schema_version: 1.0.0
src_root_id: src-root-src-001
workflow_key: product.raw-to-src
workflow_run_id: adr005-artifact-io-gateway-20260323-rerun7
source_kind: governance_bridge_src
source_refs:
- ADR-005
- ADR-001
- ADR-002
- ADR-003
- ADR-004
frozen_at: '2026-03-23T14:20:00Z'
---

# ADR 005 Skill 文件读写采用 Artifact IO Gateway + Path Policy 统一治理

## 问题陈述

当前执行链已经出现私自创建临时目录、复制目录、new/、final/、tmp/ 一类目录、在没有注册、没有声明、没有审批的情况下覆盖已有文件、通过路径猜测而不是 artifact 绑定来消费上下游文件等失控行为。 这会直接造成下游 skill 与人类 gate 都无法稳定判断“哪个才是正式版本”、无法支撑多 skill 持续运行、无法阻止 drift。 因此需要把正式文件读写从各 skill 自行处理，收口为围绕 Artifact IO Gateway、Path Policy、路径与目录治理 的统一治理能力，而不是继续依赖分散约定。

## 目标用户

- 受该治理规则约束的 skill 作者
- workflow / orchestration 设计者
- human gate / reviewer
- artifact 管理与治理消费者

## 触发场景

- 当 workflow 需要通过统一 IO 边界读取或写入 artifact 时。
- 当 skill 需要决定 artifact 目录、路径或落点策略时。

## 业务动因

- 需要现在就把这类治理变化收敛成正式需求源，否则下游 skill 与人类 gate 都无法稳定判断“哪个才是正式版本”、无法支撑多 skill 持续运行会继续沿后续需求链扩散。
- 将 ADR 归一为 bridge SRC 的价值，是让下游围绕 Artifact IO Gateway、Path Policy、路径与目录治理 共享同一组继承约束，而不是继续各自猜路径或重写规则。
- 这能为后续链路提供稳定输入：下游 skill 必须继承 Artifact IO Gateway 的统一约束，不得在本链路中重新发明等价规则；下游 skill 必须继承 Path Policy 的统一约束，不得在本链路中重新发明等价规则。

## 治理变更摘要

- 治理对象：Artifact IO Gateway; Path Policy; 路径与目录治理; artifact 输入输出边界
- 现状失控：私自创建临时目录、复制目录、new/、final/、tmp/ 一类目录; 在没有注册、没有声明、没有审批的情况下覆盖已有文件; 通过路径猜测而不是 artifact 绑定来消费上下游文件
- 统一原则：因此需要把正式文件读写从各 skill 自行处理，收口为围绕 Artifact IO Gateway、Path Policy、路径与目录治理 的统一治理能力，而不是继续依赖分散约定。
- 下游必须继承的约束：下游 skill 必须继承 Artifact IO Gateway 的统一约束，不得在本链路中重新发明等价规则。; 下游 skill 必须继承 Path Policy 的统一约束，不得在本链路中重新发明等价规则。; 下游 skill 必须继承 路径与目录治理 的统一约束，不得在本链路中重新发明等价规则。

## 关键约束

- 保持与原始输入同题，不扩展到 EPIC、FEAT、TASK 或实现设计。
- 正式文件读写必须围绕 Artifact IO Gateway、Path Policy 的统一边界建模，不得在下游恢复自由路径写入。
- 下游 skill 必须继承 Artifact IO Gateway 的统一约束，不得在本链路中重新发明等价规则。
- 下游 skill 必须继承 Path Policy 的统一约束，不得在本链路中重新发明等价规则。
- 下游 skill 必须继承 路径与目录治理 的统一约束，不得在本链路中重新发明等价规则。

## 范围边界

- In scope: 将 skill 文件读写、artifact 输入输出边界与路径策略统一收口为受治理对象，围绕 Artifact IO Gateway、Path Policy、路径与目录治理 建立稳定约束。
- In scope: 为后续主链对象提供统一约束来源与交接依据，而不是在本层展开 API 或实现设计。
- Out of scope: 下游 EPIC/FEAT/TASK 分解与实现细节。

## 来源追溯

- Source refs: ADR-005, ADR-001, ADR-002, ADR-003, ADR-004
- Input type: adr

## Bridge Context

- governed_by_adrs: ADR-005, ADR-001, ADR-002, ADR-003, ADR-004
- change_scope: 通过路径猜测而不是 artifact 绑定来消费上下游文件。 本次治理变化要求后续 skill 统一继承上述对象与路径边界，不再各自定义等价规则。
- governance_objects: Artifact IO Gateway; Path Policy; 路径与目录治理; artifact 输入输出边界
- current_failure_modes: 私自创建临时目录、复制目录、new/、final/、tmp/ 一类目录；; 在没有注册、没有声明、没有审批的情况下覆盖已有文件；; 通过路径猜测而不是 artifact 绑定来消费上下游文件。
- downstream_inheritance_requirements: 下游 skill 必须继承 Artifact IO Gateway 的统一约束，不得在本链路中重新发明等价规则。; 下游 skill 必须继承 Path Policy 的统一约束，不得在本链路中重新发明等价规则。; 下游 skill 必须继承 路径与目录治理 的统一约束，不得在本链路中重新发明等价规则。
- expected_downstream_objects: EPIC, FEAT, TASK
- acceptance_impact: 下游 gate、auditor 与 handoff 必须基于同一组受治理边界判断正式产物是否合法。; 下游消费方应能在不回读原始 ADR 的前提下理解主要失控行为与统一治理理由。; 评审时应确认 私自创建临时目录、复制目录、new/、final/、tmp/ 一类目录、在没有注册、没有声明、没有审批的情况下覆盖已有文件 不再被当作局部 skill 习惯处理。; 冻结前应确认该候选已经覆盖 下游 skill 与人类 gate 都无法稳定判断“哪个才是正式版本”、无法支撑多 skill 持续运行 等治理后果。
- non_goals: 下游 EPIC/FEAT/TASK 分解与实现细节。
