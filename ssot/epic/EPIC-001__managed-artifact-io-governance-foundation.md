---
id: EPIC-001
ssot_type: EPIC
title: Managed Artifact IO 统一治理能力底座
status: frozen
version: v1
schema_version: 0.1.0
epic_root_id: epic-root-epic-001
workflow_key: workflow.product.task.src_to_epic
source_refs:
  - SRC-001
source_freeze_ref: SRC-001
src_root_id: src-root-src-001
frozen_at: '2026-03-23T14:20:00Z'
---

# Managed Artifact IO 统一治理能力底座

## 概述

本 EPIC 的核心交付不是某一个单点功能，而是一套可被后续工作流复用的 Managed Artifact IO 治理能力底座。它需要把正式文件写入、路径合法性判断、artifact 身份登记、运行期审计，以及 gate 后的正式物化与交接，从“各 skill 各自处理”的分散习惯，收敛为一个独立、可继承、可验证的建设单元。只有先形成这一层统一底座，后续 FEAT 才能围绕明确的能力边界继续拆解，而不是混在具体代码目录、局部迁移对象或某个 skill 的私有实现里反复重造。

## 范围

- 建立 Gateway 能力面：定义正式 `read/write/commit/promote` 等受管操作入口，负责承接“要读写什么 artifact”，而不是让 skill 直接决定最终路径。
- 建立 Path Policy 判定层：定义路径白名单、artifact 到目录映射、命名规则、写入 mode 与覆盖边界，专门回答“某类 artifact 能否写到某类位置”。
- 建立 Artifact Identity 与 Registry 正式登记层：统一最小 identity contract、registry 记录、formal reference 与读取资格判定，专门回答“这个对象是否已成为正式受管 artifact”。
- 建立 Runtime Audit 与 IO Contract 执行层：对运行前后工作区变化、越权写入、未注册产物与 contract 外行为进行审计，并为 executor、supervisor、gate 提供一致证据。
- 建立 External Gate Decision 与 Materialization 层：将 `gate-decision`、`materialized-ssot`、`materialized-handoff`、`materialized-job` 与 `run-closure` 纳入统一对象边界和推进纪律，专门回答“candidate package 如何被裁决、物化并进入下一段正式链路”。
- 建立面向后续 FEAT 的治理集成基线：为 runtime helper 接入、外部 gate、现有 skill 迁移提供统一继承面，而不是在本 EPIC 内直接展开逐技能改造。

## 非目标

- 不在本 EPIC 内定义实现级 CLI 参数、SDK 方法签名或 daemon 形态。
- 不在本文件中枚举每一个现有 workflow / skill 的逐项迁移任务。
- 不在这里展开下游 FEAT / TASK 的执行设计、界面细节或仓库级清理计划。
- 不把外部 gate 的裁决权限重新内嵌回 skill 自判流程。

## 约束

- 本 EPIC 必须严格派生自 `SRC-001`，并保持对 Artifact IO Gateway、Path Policy 与 managed artifact 边界的治理焦点。
- Scope 必须停留在 EPIC 层：每个交付切片都应继续拆成多个可独立验收的 FEAT，而不能塌缩成单一实现票据。
- 后续设计必须保留 skill-first 架构、外部 gate 分权，以及“正式 managed artifact 写入不得绕过 gateway”的硬约束。
- 下游 FEAT 必须继承同一套写入合法性、artifact 身份、审计证据与 gate 后物化纪律，不得重新引入局部路径约定。

## 拆分原则

- 下游 FEAT 应按能力维度拆分，优先围绕 Gateway、Path Policy、Artifact Identity / Registry、Runtime Audit / IO Contract、External Gate Decision / Materialization 五类建设面展开，而不是按代码目录、技术层或迁移对象列表拆分。
- 只有当某个 FEAT 能独立证明一类治理能力被建立、可校验、可被后续 skill 继承时，才算符合本 EPIC 的拆分方向。

## 验收形态

- 本 EPIC 被视为完成的最小条件，是正式文件读写、路径判定、artifact 身份登记、运行期审计与 gate 后正式物化五类能力都已具备明确边界，并能共同支撑至少一条受治理主链稳定运行。
- 若后续产出仍依赖各 skill 自行选路径、猜 artifact 身份、内嵌 gate materialize 逻辑或缺少一致审计证据，则不应视为本 EPIC 已完成。

## 来源追溯

- `概述` 派生自 `SRC-001` 的 `问题陈述`、`业务动因` 与 `治理变更摘要`。
- `范围` 映射 `SRC-001` 的 `治理变更摘要`、`关键约束` 与 `Bridge Context.governance_objects`。
- `非目标` 映射 `SRC-001` 的 `范围边界` 与 `Bridge Context.non_goals`。
- `约束`、`拆分原则` 与 `验收形态` 映射 `SRC-001` 的 `关键约束`、`治理变更摘要` 与 `Bridge Context.downstream_inheritance_requirements`。
