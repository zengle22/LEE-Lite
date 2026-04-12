---
id: FEAT-SRC-RAW-TO-SRC-ADR048-005
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-005
epic_ref: EPIC-RAW-TO-SRC-ADR048
title: governed skill接入与pilot验证流
status: frozen
frozen_at: '2026-04-11T06:31:35.370308+00:00'
---

# governed skill接入与pilot验证流

Feature: governed skill接入与pilot验证流

## 背景

新的 governed skill 需要通过统一的注册、onboarding、pilot 验证流程才能进入生产环境。本 FEAT 定义 skill 的注册契约、onboarding 管线、pilot 执行框架、以及跨 skill E2E 验证流程。

## 用户故事

### US-001: Skill 注册与验证

**作为** skill developer
**我希望** 注册 skill 时自动验证契约兼容性
**以便** 确保 skill 满足主链运行的基本要求

**验收标准**:
- AC-001: Skill 注册时验证 workflow_key、authority_scope、input/output contracts
- AC-002: 验证失败时返回清晰错误信息，允许修正后重试
- AC-003: 注册成功后 skill 进入 registered 状态

### US-002: Skill Onboarding 管线

**作为** skill operator
**我希望** skill 通过兼容性检查后自动进入 onboarded 状态
**以便** skill 可以准备 pilot 执行

**验收标准**:
- AC-001: Onboarding 检查包括合约兼容性、依赖解析、运行时环境
- AC-002: 阻塞时记录阻塞原因，要求合约修复后重试
- AC-003: Onboarding 成功后 skill 进入 onboarded 状态

### US-003: Pilot 执行与证据采集

**作为** quality validator
**我希望** 在受控环境中执行 skill pilot 并采集结构化证据
**以便** 验证 skill 功能正确性和兼容性

**验收标准**:
- AC-001: Pilot 执行产生结构化证据和验收数据
- AC-002: Pilot 失败时采集证据并路由到 fix-feature 用于重试
- AC-003: Pilot 通过后 skill 进入 pilot_passed 状态

### US-004: 跨 Skill E2E 验证

**作为** integration engineer
**我希望** 验证多个 skill 之间的端到端兼容性
**以便** 确保 skill 组合在生产环境中协同工作

**验收标准**:
- AC-001: 跨 skill E2E 测试覆盖注册 skill 的关键集成点
- AC-002: E2E 通过后生成 pilot 报告
- AC-003: skill 通过 E2E 验证后提升到 production 状态

## 状态模型

- 主状态流: `skill_registered` -> `onboarded` -> `pilot_ready` -> `pilot_passed` -> `production_done`
- 恢复路径: `registration_failed` -> 拒绝并返回清晰验证错误，允许重试
- 恢复路径: `onboarding_blocked` -> 记录阻塞原因，要求合约修复后重试
- 恢复路径: `pilot_failed` -> 采集证据，路由到 fix-feature 用于 pilot 重试
- 失败信号: `registration_failed`、`onboarding_blocked`、`pilot_failed`
- Fail-closed: 任何恢复路径耗尽重试次数后升级到手动审核

## 主时序

1. Skill developer 提交 skill 注册请求（包含 workflow_key、authority_scope、contracts）
2. 系统验证注册契约并返回验证结果
3. 注册通过后进入 onboarding 管线
4. Onboarding 检查合约兼容性、依赖解析、运行时环境
5. Onboarding 通过后进入 pilot_ready 状态
6. Pilot runner 在受控环境中执行 skill 并采集证据
7. 跨 skill E2E 验证确保集成兼容性
8. Pilot 和 E2E 通过后 skill 提升到 production 状态

## 边界约束

- **入边界**: Skill 注册必须包含完整的 workflow_key、authority_scope、input/output contracts
- **出边界**: 返回 skill 注册状态、pilot 证据、E2E 验证报告、production 提升确认
- **不做什么**: 不重新定义 skill 执行语义、不处理 gate decision 或 formal publication、不定义 FEAT/TECH 推导规则
- **向后兼容**: 旧 skill 可在兼容模式下注册，附带警告

## 关键不变量

- Skill 必须通过注册、onboarding、pilot、E2E 四阶段验证才能进入 production
- 每一阶段失败必须采集结构化证据，不得跳过
- Pilot 执行必须在受控环境中进行，不得影响生产数据
- 旧 skill 兼容模式仅提供过渡路径，不得作为长期方案
