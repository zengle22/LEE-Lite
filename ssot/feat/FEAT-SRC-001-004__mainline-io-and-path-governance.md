---
id: FEAT-SRC-001-004
ssot_type: FEAT
title: 主链文件 IO 与路径治理能力
status: frozen
version: v2
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-004
workflow_key: product.epic-to-feat
workflow_run_id: src001-from-frozen-src-20260324
source_refs:
  - EPIC-001
  - SRC-001
  - ADR-005
  - ADR-001
  - ADR-002
  - ADR-003
  - ADR-004
  - ARCH-SRC-001-001
epic_ref: EPIC-001
epic_root_id: epic-root-epic-001
source_freeze_ref: SRC-001
src_root_id: src-root-src-001
frozen_at: '2026-03-24T12:30:00Z'
---

# 主链文件 IO 与路径治理能力

## 目标

让主链中的 artifact IO、路径与目录边界收敛为受治理能力，并且严格限制在 mainline handoff 和 formalization 语境内。

## 范围

- 约束主链 handoff、formal materialization 与 governed skill IO 的 artifact path、目录边界与写入模式。
- 明确哪些 IO 是受治理主链 IO，哪些属于全局文件治理而必须留在本 FEAT 之外。
- 要求所有正式主链写入都遵循统一的路径与覆盖边界，不允许以局部临时目录策略替代。
- 明确本 FEAT 只覆盖 mainline IO/path 边界，不扩展为全仓库或全项目文件治理总方案。

## 输入

- authoritative `EPIC-001`
- 来自 `SRC-001` 的路径与目录治理约束
- 与 handoff、formal materialization、governed skill IO 相关的主链写入边界

## 处理

- 固定主链 IO/path 的受治理范围。
- 将 handoff、formal materialization 与 governed skill IO 的写入边界压到同一能力面。
- 阻止主链 IO 退化为局部目录策略或自由写入。

## 输出

- 主链 IO/path scope boundary
- formal write path / mode 约束
- 下游必须继承的路径与目录治理边界

## 依赖

- 边界依赖 `对象分层与准入能力`：定义对象落盘边界，不定义对象层级与消费资格本身。
- 边界依赖 `正式交接与物化能力`：约束 formalization 的 IO/path 边界，但 formalization 决策语义仍属于正式交接 FEAT。

## 非目标

- 不定义 object qualification、candidate/formal authority 或 consumer admission semantics。
- 不定义 gate decision semantics、approval authority 或 formalization outcomes。

## 约束

- 主链 IO/path 规则只覆盖 handoff、formal materialization 与 governed skill IO，不得外扩成全局文件治理。
- 任何正式主链写入都必须遵守受治理 path / mode 边界，不允许 silent fallback 到自由写入。
- 下游 skill 必须继承路径与目录治理的统一约束，不得在本链路中重新发明等价规则。

## 验收检查

### AC-01 主链 IO 边界必须明确

- scenario: governed skill performs mainline IO
- given: 主链需要写出 handoff 或 formalization artifact
- when: 判断该写入是否属于本 FEAT 作用域
- then: 必须能明确哪些 IO 属于 mainline handoff / materialization，哪些 IO 明确超出作用域

### AC-02 路径治理不得扩张为全局文件治理

- scenario: downstream team proposes repository-wide directory rules
- given: 团队希望把更多文件治理纳入本 FEAT
- when: 对照本 FEAT scope
- then: 必须拒绝超出 governed skill IO、handoff、materialization 边界的 scope expansion

### AC-03 正式写入不得回退为自由写入

- scenario: mainline write hits a path or mode restriction
- given: 主链写入遇到 path / mode 限制
- when: 调用方尝试重试
- then: 必须保留 path / mode enforcement，不得 silent fallback 到 uncontrolled writes

## 来源追溯

- 本文件物化自 [feat-freeze-bundle.md](E:/ai/LEE-Lite-skill-first/artifacts/epic-to-feat/src001-epic-to-feat-20260324-v3/feat-freeze-bundle.md) 中 `FEAT-SRC-001-004` 对应段落。
