---
id: FEAT-SRC-001-002
ssot_type: FEAT
title: Path Policy 与写入模式判定
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-002
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

# Path Policy 与写入模式判定

## 目标

建立统一的 Path Policy 判定层，专门负责回答“某类 artifact 是否可以用某种 mode 写到某类位置”，把路径白名单、命名规则、覆盖边界与 mode 规则从各 skill 的局部约定中抽离出来。

## 范围

- 定义允许写入的根目录、禁止区域与路径白名单。
- 定义 artifact type 到目录映射、命名规则与层级约束。
- 定义 `create`、`replace`、`patch`、`append`、`promote` 等 mode 的适用边界与失败条件。
- 为 Gateway 与 auditor 提供统一的路径合法性与 mode 判定结果。

## 输入

- `SRC-001` 中冻结的路径治理约束
- Gateway 提交的 artifact 语义请求
- 调用方声明的 mode、target path 与 logical identity

## 处理

- 对目标路径执行合法性与命名规则判断。
- 对 mode 与 artifact 类型组合执行覆盖权限与操作边界判断。
- 输出可供 Gateway 与 auditor 复用的政策判定结果。

## 输出

- Path Policy 规则集
- 路径与 mode 判定结果
- 写入拒绝与违规原因分类

## 依赖

- 为 `FEAT-SRC-001-001` Gateway 提供路径与 mode 的硬判定。
- 为 `FEAT-SRC-001-004` 审计层提供违规分类依据。

## 非目标

- 不在本 FEAT 内承担正式 artifact 的落盘执行。
- 不在本 FEAT 内生成 artifact identity、registry 记录或 handoff 引用。
- 不处理逐 skill 迁移顺序与 rollout 计划。

## 约束

- Path Policy 是路径合法性的唯一政策源。
- mode 规则必须独立于 skill 临时决定，不允许隐式覆盖或例外通过。
- 未通过 Path Policy 的路径或 mode 组合不得进入正式链路。

## 验收检查

### AC-01 非法路径必须被阻断

- scenario: 调用方尝试将正式 artifact 写入未授权目录
- given: Path Policy 已声明允许根目录与禁止区域
- when: 发起路径判定
- then: 系统必须返回拒绝结果，并明确给出违规原因
- trace_hints: illegal root, policy deny, violation reason

### AC-02 mode 与 artifact 类型边界必须可判定

- scenario: 调用方请求以特定 mode 写入 managed artifact
- given: artifact type 与 mode 组合已提交
- when: 执行 mode 判定
- then: 系统必须明确给出允许或拒绝，不得依赖 skill 自行解释
- trace_hints: mode policy, overwrite boundary, create replace patch

### AC-03 Gateway 与 Auditor 使用同一政策源

- scenario: 正式写入执行后需要审计
- given: Gateway 与 auditor 都需要判断路径合法性
- when: 两者消费 Path Policy
- then: 结论必须基于同一政策源，而不是出现两套不同规则
- trace_hints: shared policy source, gateway decision, auditor decision

## 来源追溯

- `目标` 与 `范围` 派生自 `EPIC-001` 的 `范围` 第 2 条与 `约束`。
- `处理`、`约束` 与 `验收检查` 映射 `SRC-001` 的 `关键约束`、`治理变更摘要` 与 `Bridge Context.governance_objects`。

