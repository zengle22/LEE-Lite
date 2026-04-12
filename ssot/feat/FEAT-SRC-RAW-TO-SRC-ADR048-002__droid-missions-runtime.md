---
id: FEAT-SRC-RAW-TO-SRC-ADR048-002
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-002
epic_ref: EPIC-SRC-RAW-TO-SRC-ADR048
title: Droid Missions Runtime —— API/E2E 验证执行与证据采集
status: frozen
frozen_at: '2026-04-12T17:56:00.000000+00:00'
---

# Droid Missions Runtime —— API/E2E 验证执行与证据采集

## 背景

Mission Compiler 产出 features.json 后，Droid Missions Runtime 负责执行其中的 validation-contracts，通过 API/E2E workers 运行验证，采集证据，写回 validation-state。这是双链测试从"治理态"升级为"运行时态"的核心执行层。

## 用户故事

### US-001: API Worker 执行验证合约

**作为** Droid API Worker
**我希望** 读取 features.json 中的 API validation-contracts
**以便** 执行 API 断言并采集证据

**验收标准**:
- AC-001: 按 execution-manifest.yaml 的优先级顺序执行（P0 → P1 → P2）
- AC-002: 每个 contract 执行后产出 evidence（request snapshot, response snapshot, DB assertion result）
- AC-003: 验证状态写入 `.droid/state/validation-state.yaml`
- AC-004: 失败时记录失败原因，继续执行下一个 contract

### US-002: E2E Worker 执行用户旅程

**作为** Droid E2E Worker
**我希望** 读取 features.json 中的 E2E validation-contracts (ui-travel 类型)
**以便** 执行用户旅程验证并采集 UI 状态证据

**验收标准**:
- AC-001: 执行 user_steps 并验证 expected_ui_states
- AC-002: 采集 playwright_trace, screenshot_final, network_log, persistence_assertion
- AC-003: 执行 anti_false_pass_checks 防止误通过
- AC-004: 验证状态写入 validation-state.yaml

### US-003: 证据采集与完整性验证

**作为** Droid Evidence Collector
**我希望** 为每个执行的 contract 采集结构化证据
**以便** Gate Evaluation 阶段可以审计验证结果

**验收标准**:
- AC-001: 每条证据包含 content hash 用于防篡改
- AC-002: Scrutiny Validator 验证证据完整性（不缺项）
- AC-003: 所有证据写入 `.droid/evidence/` 目录

### US-004: Validation State 回写

**作为** Droid Validation State Writer
**我希望** 将每个 contract 的执行结果写回 validation-state.yaml
**以便** Gate Evaluation 消费

**验收标准**:
- AC-001: 状态映射遵循 ADR-048 Section 2.3.3
- AC-002: passed + evidence:complete → validation-state: passed
- AC-003: failed → validation-state: failed
- AC-004: waived → validation-state: waived，不计入失败

## 状态模型

- 主状态流: `runtime_idle` -> `workers_dispatched` -> `evidence_collected` -> `validation_state_written`
- 恢复路径: `worker_failed` -> 记录失败证据，继续执行下一个 worker
- 恢复路径: `evidence_collection_failed` -> 标记证据缺失，validation-state 记录 failed
- 失败信号: `all_workers_failed`、`evidence_collection_blocked`
- Fail-closed: 全部 worker 失败时产出 all-failed validation-state，触发 Gate Evaluation 的 block 路径

## 主时序

1. Droid Job Runner 派发 Runtime Job（target_skill: "workflow.adr048.droid-runtime"）
2. Runtime 读取 features.json 和 execution-manifest.yaml
3. 按优先级派发 API Workers
4. 按优先级派发 E2E Workers
5. Evidence Collector 采集各 worker 证据
6. Scrutiny Validator 验证证据完整性
7. Validation State Writer 写入最终状态
8. 触发下游 Gate Evaluation Job

## 边界约束

- **入边界**: 只消费 Mission Compiler 产出的 features.json 和 execution-manifest.yaml
- **出边界**: 产出 `.droid/state/validation-state.yaml` + `.droid/evidence/` 目录
- **不做什么**: 不修改 SSOT 文档、不定义 gate 决策逻辑、不创建 fix features
- **向后兼容**: 不影响现有独立 testset 对象的读取

## 关键不变量

- Worker 执行不得猜测需求意图，严格按 validation-contract 执行
- 证据采集必须包含 content hash，防止篡改
- 所有 worker 并行执行时不得共享可变状态
- Validation-state 必须包含每个 contract 的独立状态，不得只聚合

## 集成点

- 被 Droid Job Runner 通过 `target_skill: "workflow.adr048.droid-runtime"` 调用
- 读取 Mission Compiler 产出的 features.json + execution-manifest.yaml
- 产出 validation-state.yaml + evidence 供 Gate Evaluation 消费
- 包含 7 个新模块: droid_runtime.py, api_worker.py, e2e_worker.py, evidence_collector.py, validation_state_writer.py, scrutiny_validator.py, user_testing_validator.py
