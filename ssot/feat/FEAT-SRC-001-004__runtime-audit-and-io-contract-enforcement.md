---
id: FEAT-SRC-001-004
ssot_type: FEAT
title: Runtime Audit 与 IO Contract 执行
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-004
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

# Runtime Audit 与 IO Contract 执行

## 目标

建立运行期的 IO Contract 执行与 Workspace Audit 能力，使系统能够在 skill 执行前后识别越权写入、未注册 artifact、contract 外访问与路径漂移，并把这些行为转化为 gate、repair 与监督消费者可直接使用的结构化证据。

## 范围

- 定义 IO Contract 的能力边界，包括 artifact scope、path scope、operation scope 与 staging 晋升规则。
- 对 skill 执行前后工作区变化进行 diff，识别新增文件、修改文件、新增目录与违规写入。
- 输出 blocker / warn / info 等级的结构化审计结果。
- 为 executor、supervisor、gate 与 repair 闭环提供可消费的违规证据与定位信息。

## 输入

- skill 的 IO Contract 声明
- Gateway、Path Policy、Registry 产生的运行记录
- 执行前后工作区快照与文件变化

## 处理

- 对比 contract 声明与实际访问范围。
- 检查是否存在绕过 Gateway 的正式写入、未注册 artifact 消费、越界路径写入与命名漂移。
- 输出结构化审计分级与修补定位信息。

## 输出

- 审计报告
- 违规分级结果
- 面向 repair / gate / supervision 的证据对象

## 依赖

- 依赖 `FEAT-SRC-001-001`、`FEAT-SRC-001-002`、`FEAT-SRC-001-003` 提供正式操作、政策判定与 registry 记录。
- 为后续 repair 闭环与 gate materialization 提供一致输入。

## 非目标

- 不在本 FEAT 内负责 artifact 正式落盘。
- 不在本 FEAT 内决定业务语义层面的 freeze / retry / human handoff 裁决。
- 不替代外部 gate 的最终批准角色。

## 约束

- Workspace Auditor 必须基于 IO Contract、Path Policy 与 Registry 做综合判断，而不是只看目录 diff。
- 对 managed artifact 的越权写入、未注册消费与 path traversal 至少要能阻断或形成 blocker 证据。
- 审计结果必须能够进入最小修补闭环，而不是停留在不可操作的自然语言描述。

## 验收检查

### AC-01 越权写入必须可见

- scenario: skill 在 contract 外执行写入
- given: IO Contract 已声明 artifact scope、path scope 与 operation scope
- when: 执行前后工作区被审计
- then: 审计结果必须明确标记该行为并给出违规等级
- trace_hints: contract violation, path scope, operation scope

### AC-02 未注册 artifact 消费必须被识别

- scenario: 下游流程尝试消费未登记文件
- given: Registry 中不存在对应 managed artifact 记录
- when: 执行受管读取或交接检查
- then: 系统必须产生 blocker 或等效阻断证据
- trace_hints: unmanaged consumption, registry miss, blocker finding

### AC-03 审计结果必须能驱动修补

- scenario: 运行中发现路径漂移或命名违规
- given: auditor 已输出结构化 findings
- when: repair 或 supervisor 消费这些 findings
- then: findings 必须足以定位问题对象、违规类型与最小修补范围
- trace_hints: audit finding, repair targeting, minimal patch scope

## 来源追溯

- `目标` 与 `范围` 派生自 `EPIC-001` 的 `范围` 第 4 条、`拆分原则` 与 `验收形态`。
- `处理`、`约束` 与 `验收检查` 映射 `SRC-001` 的 `关键约束`、`治理变更摘要` 与 `Bridge Context.acceptance_impact`。
