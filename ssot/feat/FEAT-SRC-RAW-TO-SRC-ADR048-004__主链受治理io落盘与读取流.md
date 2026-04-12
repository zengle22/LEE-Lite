---
id: FEAT-SRC-RAW-TO-SRC-ADR048-004
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-004
epic_ref: EPIC-RAW-TO-SRC-ADR048
title: 主链受治理io落盘与读取流
status: frozen
frozen_at: '2026-04-11T06:31:35.369815+00:00'
---

# 主链受治理io落盘与读取流

Feature: 主链受治理io落盘与读取流

## 背景

主链运行过程中所有文件 IO 操作必须经过受治理的路径验证、权限控制和审计记录。本 FEAT 定义文件路径治理规则、读写载体的权限强制行为、以及 IO 操作的审计轨迹记录。

## 用户故事

### US-001: 受治理的文件写入

**作为** governed skill executor
**我希望** 写入文件时自动经过路径验证和权限检查
**以便** 不会写入未授权路径或破坏文件结构

**验收标准**:
- AC-001: 所有文件写入必须通过路径验证，拒绝未授权路径
- AC-002: 写入操作记录审计轨迹条目
- AC-003: 写入失败时回滚部分写入并记录失败详情

### US-002: 受治理的文件读取

**作为** downstream consumer
**我希望** 读取文件时验证路径权限和访问模式
**以便** 只读取授权范围内文件

**验收标准**:
- AC-001: 所有文件读取必须通过路径解析守卫
- AC-002: 读取操作记录审计轨迹条目
- AC-003: 审计失败时 fail-closed，阻止 IO 完成

### US-003: 审计轨迹查询

**作为** quality auditor
**我希望** 查询所有受治理 IO 操作的审计轨迹
**以便** 追踪文件变更历史和验证合规性

**验收标准**:
- AC-001: 每条受治理 IO 操作产生独立审计条目
- AC-002: 审计条目包含操作类型、路径、时间、操作者
- AC-003: 审计轨迹不可修改，append-only

## 状态模型

- 主状态流: `io_pending` -> `path_validation_done` -> `io_execution_completed` -> `audit_recorded_done`
- 恢复路径: `path_validation_failed` -> 拒绝并返回清晰错误，不尝试 IO
- 恢复路径: `io_execution_failed` -> 记录失败、回滚部分写入 -> 手动解决
- 恢复路径: `audit_record_failed` -> fail-closed，阻止 IO 完成直到审计成功
- 失败信号: `path_validation_failed`、`io_execution_failed`、`audit_record_failed`
- Fail-closed: 审计失败时不完成 IO，要求手动解决

## 主时序

1. Skill executor 请求文件写入/读取操作
2. 系统验证路径是否符合治理规则（路径模式、权限、访问模式）
3. 路径验证通过后执行读写操作
4. 系统记录审计轨迹条目（操作类型、路径、时间、操作者）
5. 审计记录成功后标记 IO 完成
6. 下游消费方可安全读取已落盘文件

## 边界约束

- **入边界**: 所有文件 IO 必须通过 cli/lib/fs.py 路径验证守卫
- **出边界**: 返回操作结果、审计轨迹引用、路径验证状态
- **不做什么**: 不重新定义 gate decision 语义、不负责 formal publication（FEAT-003）、不定义 FEAT/TECH 推导规则
- **向后兼容**: 旧 IO 路径记录为警告，必须迁移到受治理路径

## 关键不变量

- 所有文件 IO 必须经过路径验证守卫，不得绕过
- 审计轨迹必须 append-only，不可修改或删除
- 审计失败时 fail-closed，不完成 IO 操作
- 路径治理规则对所有 skill executor 统一适用
