---
id: FEAT-SRC-001-003
ssot_type: FEAT
title: Artifact Identity 与 Registry 正式登记
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-003
workflow_key: workflow.product.task.epic_to_feat
source_refs:
  - EPIC-001
  - SRC-001
epic_ref: EPIC-001
epic_root_id: epic-root-epic-001
source_freeze_ref: SRC-001
src_root_id: src-root-src-001
frozen_at: '2026-03-23T14:20:00Z'
---

# Artifact Identity 与 Registry 正式登记

## 目标

建立 managed artifact 的最小 identity contract 与 registry 正式登记机制，让正式产物是否成立、是否可被受管读取，不再依赖路径猜测，而是依赖 registry 中可追溯的 identity、path、status 与 source refs 关系。

## 范围

- 定义 managed artifact 的最小 identity contract，包括 artifact type、logical name、stage、producer scope 与唯一性边界。
- 定义 registry 中必须记录的核心字段，如 path、producer run、inputs、status、source refs、evidence refs 与最小 lineage 指针。
- 定义 commit / promote 后如何完成 identity 绑定、registry 登记与正式读取资格判定。
- 定义 registry-backed formal reference 的最小形态，供受管读取与治理消费者复用。

## 输入

- 由 Gateway 提交的正式 artifact 写入结果
- 调用方声明的 logical identity 与 source refs
- Path Policy 已确认的目标路径

## 处理

- 为正式 artifact 生成并校验最小 identity contract。
- 将 logical identity、physical path、inputs、status、source refs 与最小 lineage 指针登记到 registry。
- 基于 registry 判断某个 artifact 是否具备正式读取资格，并输出 registry-backed formal reference。

## 输出

- registry 记录
- managed artifact 正式引用
- 最小 lineage 追溯信息

## 依赖

- 依赖 `FEAT-SRC-001-001` 将正式写入收口到 Gateway。
- 依赖 `FEAT-SRC-001-002` 提供已合法化的目标路径。
- 被 `FEAT-SRC-001-004` 用于检查“未注册 artifact 被消费”等违规情况。

## 非目标

- 不在本 FEAT 内负责路径合法性判定。
- 不在本 FEAT 内负责工作区 diff 与违规审计执行。
- 不在本 FEAT 内承载 external gate、materialized handoff、materialized job 或 run closure。
- 不在本 FEAT 内展开完整 handoff binding 投影或独立的跨链 lineage 图。

## 约束

- Artifact Registry 是 managed artifact 身份的唯一登记源。
- Gateway 是正式读写入口；Registry 负责正式读取资格判定与 formal reference 解析；Auditor 只消费证据并输出阻断结论。
- 未进入 registry 的文件不得被正式 skill 当作受管输入消费。
- lineage 在本 FEAT 内只要求支撑 registry 追溯与 audit 定位，不替代后续 handoff / materialization 体系。

## 验收检查

### AC-01 正式 artifact 必须可登记为唯一身份

- scenario: 一个 managed artifact 已完成合法写入
- given: artifact type、logical identity、stage、producer scope 与目标路径已明确
- when: 执行 registry 绑定
- then: 系统必须生成唯一身份并完成 registry 登记
- trace_hints: artifact_id, minimal identity contract, registry entry

### AC-02 未注册文件不得进入正式链路

- scenario: 下游 skill 尝试消费某个文件
- given: 该文件尚未完成 registry 登记
- when: 发起正式受管读取
- then: 系统必须拒绝其作为正式 managed artifact 被消费
- trace_hints: unmanaged input, registry miss, managed read denial

### AC-03 lineage 必须可追溯

- scenario: artifact 发生 patch、promote 或派生输出
- given: 上下游对象已建立 source refs
- when: 查询 registry 记录
- then: 系统必须能解释该 artifact 的直接来源、派生关系与当前正式状态
- trace_hints: lineage, derived artifact, registry trace

## 来源追溯

- `目标` 与 `范围` 派生自 `EPIC-001` 的 `范围` 第 3 条与 `约束`。
- `处理`、`约束` 与 `验收检查` 映射 `SRC-001` 的 `治理变更摘要`、`关键约束` 与 `Bridge Context.downstream_inheritance_requirements`。
