---
id: FEAT-SRC-001-001
ssot_type: FEAT
title: Managed Artifact Gateway 受管操作入口
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-001
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

# Managed Artifact Gateway 受管操作入口

## 目标

建立一组统一的 Managed Artifact Gateway 受管操作入口，让正式 artifact 的读取、写入、commit、promote 与 run-log 追加都通过同一能力面完成，终止 skill 直接决定最终落盘路径的做法。

## 范围

- 定义正式 `read_artifact`、`write_artifact`、`commit_artifact`、`promote_artifact`、`append_run_log` 一类受管操作入口。
- 明确每种操作的输入语义，包括 artifact type、logical name、stage、mode、source refs 与调用上下文。
- 规定 Gateway 成功与失败时的标准返回对象，确保下游 handoff、gate、auditor 可以消费一致结果。
- 明确 Gateway 失败时只能保留 staging 或 error evidence，不得 silent fallback 到直接路径写入。

## 输入

- 已冻结的 `SRC-001`
- 调用方声明的 artifact 语义信息
- Path Policy 与 Artifact Identity / Registry 提供的判定结果

## 处理

- 将调用方的 artifact 语义请求翻译成受管操作。
- 在真正落盘前触发路径合法性、操作 mode 与覆盖权限检查。
- 为每次正式写入输出标准化回执，供下游审计和交接引用。

## 输出

- Gateway 受管操作约定
- 标准化的操作回执与失败结果
- 供下游 skill 继承的正式写入入口边界

## 依赖

- 依赖 `FEAT-SRC-001-002` 提供路径合法性与 mode 判定。
- 依赖 `FEAT-SRC-001-003` 提供 artifact identity、registry 与 lineage 绑定。
- 与 `FEAT-SRC-001-004` 协同，为审计输出一致证据。

## 非目标

- 不在本 FEAT 内定义 Path Policy 的目录映射细则。
- 不在本 FEAT 内实现 Registry 主键策略与 lineage 结构。
- 不把 Gateway 设计成重型平台服务或固定技术形态。

## 约束

- 所有正式 managed artifact 写入都必须通过 Gateway 入口完成。
- Gateway 不负责授予路径合法性，也不负责自行发明 artifact 身份。
- Gateway 的职责是收口正式操作，而不是吞并所有治理规则。

## 验收检查

### AC-01 正式写入必须经由 Gateway

- scenario: skill 需要创建一个正式 managed artifact
- given: 调用方已声明 artifact type、logical identity 与写入 mode
- when: 调用方发起正式写入请求
- then: 请求必须进入 Gateway 入口，且结果返回标准化操作回执
- trace_hints: write_artifact, managed write receipt, source_refs

### AC-02 Gateway 失败不得回退为自由写入

- scenario: Gateway 在路径判定或权限检查阶段失败
- given: 调用方尝试写入正式 artifact
- when: Gateway 返回失败
- then: 系统只能保留 staging 或 error evidence，不得改为直接路径写入
- trace_hints: gateway failure, staging retention, no direct write fallback

### AC-03 下游可继承统一操作面

- scenario: 下游 skill 需要消费正式 artifact 写入能力
- given: 上游已经定义 Gateway 操作入口
- when: 下游接入同类 managed artifact 流程
- then: 下游应复用同一组受管操作入口，而不是各自再发明等价写入接口
- trace_hints: shared operation surface, downstream inheritance, managed artifact gateway

## 来源追溯

- `目标` 与 `范围` 派生自 `EPIC-001` 的 `概述`、`范围` 第 1 条与 `约束`。
- `处理` 与 `验收检查` 映射 `SRC-001` 的 `关键约束`、`治理变更摘要` 与 `Bridge Context.downstream_inheritance_requirements`。

