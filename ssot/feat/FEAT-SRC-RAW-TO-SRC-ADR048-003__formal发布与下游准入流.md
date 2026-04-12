---
id: FEAT-SRC-RAW-TO-SRC-ADR048-003
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-003
epic_ref: EPIC-RAW-TO-SRC-ADR048
title: formal发布与下游准入流
status: frozen
frozen_at: '2026-04-11T06:31:35.369276+00:00'
---

# formal发布与下游准入流

Feature: formal发布与下游准入流

## 背景

Gate decision approve 后，需要将 candidate 物化为 formal object 并分发给下游消费方。本 FEAT 定义 formal publication 的触发条件、materialization 规则、以及下游准入的读取资格与分发路由。

## 用户故事

### US-001: Formal 物化 candidate 为正式对象

**作为** formal publisher
**我希望** 收到 gate approve decision 后将 candidate 物化为 formal ref
**以便** 下游消费方能引用权威版本

**验收标准**:
- AC-001: formal_ref 根据类型前缀正确分配（formal.src、formal.epic、formal.feat、formal.tech、formal.testset）
- AC-002: 物化过程包含完整的状态转换记录
- AC-003: 物化失败时不发射 formal_ref，需手动解决

### US-002: 下游分发路由

**作为** downstream consumer
**我希望** 根据 formal_ref 类型接收到正确的分发目标
**以便** 我能消费对应类型的正式对象

**验收标准**:
- AC-001: formal.src 分发到 src 消费链
- AC-002: formal.epic 分发到 epic 消费链
- AC-003: formal.feat 分发到 feat 消费链
- AC-004: 分发阻塞时支持带退避的重试

### US-003: 旧系统兼容读取

**作为** legacy skill 消费者
**我希望** 通过 registry 观察已发布的 formal refs
**以便** 在迁移期间继续获取更新

**验收标准**:
- AC-001: 未启用 formal dispatch 的 skill 通过 registry 只读观察 published refs
- AC-002: 下游拒绝时记录拒绝日志，fail-closed 升级到手动审核

## 状态模型

- 主状态流: `formal_pending` -> `formal_materialized` -> `dispatch_triggered` -> `downstream_published`
- 恢复路径: `materialization_failed` -> 幂等守卫重试 -> `formal_materialized`
- 恢复路径: `dispatch_blocked` -> 带退避重试 -> `dispatch_triggered`
- 恢复路径: `downstream_rejected` -> 记录拒绝日志，fail-closed -> 手动审核升级
- 失败信号: `materialization_failed`、`dispatch_blocked`、`downstream_rejected`
- Fail-closed: 物化失败不发射 formal_ref，要求手动解决

## 主时序

1. Gate approve decision 触发 formal materialization
2. 系统根据 decision_target 确定 formal_ref 类型前缀
3. 系统物化 candidate 为 formal object 并记录状态转换
4. 系统根据 formal_ref 类型前缀路由到对应下游分发链
5. 下游消费方接收并确认 formal object
6. 旧系统兼容层通过 registry 观察已发布 refs

## 边界约束

- **入边界**: 必须由 authoritative gate approve decision 触发，包含 decision_ref、decision_basis_refs、dispatch_target
- **出边界**: 返回 formal_ref、dispatch receipt、下游确认状态
- **不做什么**: 不重新定义 gate decision 语义、不处理 execution return 路由、不定义 FEAT/TECH 推导规则
- **向后兼容**: 现有 skill 通过 registry 只读观察 published refs，不强制迁移

## 关键不变量

- Formal 发布只能由 gate approve decision 触发，不得出现其他入口
- formal_ref 类型前缀必须与目标下游消费链严格对应
- 物化过程必须幂等，重复触发不得产生重复 formal_ref
- 旧系统兼容层仅提供只读观察，不得修改 formal objects
