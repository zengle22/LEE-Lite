---
id: EPIC-SRC-RAW-TO-SRC-ADR048
ssot_type: EPIC
epic_ref: EPIC-SRC-RAW-TO-SRC-ADR048
title: 双链测试运行时接入——SSOT 编译、Droid 执行、Gate 裁决闭环
status: frozen
frozen_at: '2026-04-12T17:56:00.000000+00:00'
---

# 双链测试运行时接入

## 背景

ADR-048 定义了 SSOT 需求层、双链测试层、Droid Missions 执行层三真相源的串联架构。当前缺口是：双链的 spec/manifest 是静态文档，没有被编译为执行器可消费的结构化 mission；执行器没有统一的运行时语义；gate 决策后的回流路径不清晰。

本 EPIC 描述将双链测试从"治理态"升级为"运行时态"所需的全部开发功能。

## 范围

- FEAT-001: Mission Compiler —— 将 SSOT 文档和双链资产编译为 Droid 可消费的 features.json
- FEAT-002: Droid Missions Runtime —— 执行 API/E2E validation contracts，采集证据，写回状态
- FEAT-003: Gate Evaluation —— 消费 validation-state，计算 settlement，产出里程碑决策

## 边界

- 本 EPIC 只覆盖运行时开发功能
- 治理流程（候选提交、gate 审核、formal 发布等）属于 ADR-048 架构决策本身，不在本 EPIC 范围内
- 旧 testset 对象层退出体系

## 交付物

1. Mission Compiler 模块（编译器）
2. Droid Runtime worker 模块（API/E2E 执行器 + 证据采集）
3. Gate Evaluation 模块（settlement 计算 + 里程碑决策）
4. skill_invoker.py 分发路由集成
5. ready_job_dispatch.py Job 创建逻辑集成
