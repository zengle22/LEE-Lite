---
id: UI-RUNNER-OPERATOR-SHELL
ssot_type: UI
ui_ref: UI-RUNNER-OPERATOR-SHELL
ui_owner_ref: UI-RUNNER-OPERATOR-SHELL
feat_ref: FEAT-SRC-003-007
title: Runner Operator Shell
status: accepted
schema_version: 1.0.0
workflow_key: dev.proto-to-ui
workflow_run_id: src003-adr042-ui-007-20260407-r1
candidate_package_ref: artifacts/proto-to-ui/src003-adr042-ui-007-20260407-r1--feat-src-003-007
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-ui-007-formalize.json
frozen_at: '2026-04-07T04:17:53Z'
related_feat_refs:
- FEAT-SRC-003-002
- FEAT-SRC-003-003
- FEAT-SRC-003-007
surface_map_refs:
- SURFACE-MAP-FEAT-SRC-003-002
- SURFACE-MAP-FEAT-SRC-003-003
- SURFACE-MAP-FEAT-SRC-003-007
merged_candidate_refs:
- candidate.ui.src003-adr042-ui-002-20260407-r1
- candidate.ui.src003-adr042-ui-003-20260407-r1
- candidate.ui.src003-adr042-ui-007-20260407-r1
source_package_refs:
- artifacts/proto-to-ui/src003-adr042-ui-002-20260407-r1--feat-src-003-002
- artifacts/proto-to-ui/src003-adr042-ui-003-20260407-r1--feat-src-003-003
- artifacts/proto-to-ui/src003-adr042-ui-007-20260407-r1--feat-src-003-007
---

# Runner Operator Shell

## Ownership Summary
- ui_owner_ref: UI-RUNNER-OPERATOR-SHELL
- related_feat_refs: FEAT-SRC-003-002, FEAT-SRC-003-003, FEAT-SRC-003-007
- surface_map_refs: SURFACE-MAP-FEAT-SRC-003-002, SURFACE-MAP-FEAT-SRC-003-003, SURFACE-MAP-FEAT-SRC-003-007
- source_package_count: 3

## Aggregated UI Specs

### FEAT-SRC-003-002 · UI Spec Bundle for FEAT-SRC-003-002
- source_package_ref: artifacts/proto-to-ui/src003-adr042-ui-002-20260407-r1--feat-src-003-002
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-002
- ui_action: create

#### UI Spec runner-用户入口流

# UI Spec runner-用户入口流

- feat_ref: FEAT-SRC-003-002
- page_title: Runner 用户入口流
- journey_structural_spec_ref: journey-ux-ascii.md
- ui_shell_snapshot_ref: ui-shell-spec.md

## Page Goal
冻结一个用户可显式调用的 Execution Loop Job Runner 入口 skill，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。

## Main Path
- 进入 Runner 用户入口流
- 查看首屏说明
- 执行核心输入或选择
- 点击主按钮
- 接收校验与提交反馈
- 进入下一步或完成本页

## Branch Paths
- Branch A: 点击主按钮 / 校验失败 / 修正信息 / 重新提交
- Branch B: 提交请求 / 服务端失败 / 展示错误 / 允许重试

## States
- initial: 展示默认结构与说明
- ready: 页面主要结构和主操作已就绪
- partial: 展示局部状态和骨架
- retryable_error: 展示错误并保留上下文
- settled: 展示最终结构

## Actions
- 继续 (primary)
- 重置场景 (reset)

### FEAT-SRC-003-003 · UI Spec Bundle for FEAT-SRC-003-003
- source_package_ref: artifacts/proto-to-ui/src003-adr042-ui-003-20260407-r1--feat-src-003-003
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-003
- ui_action: update

#### UI Spec runner-控制面流

# UI Spec runner-控制面流

- feat_ref: FEAT-SRC-003-003
- page_title: Runner 控制面流
- journey_structural_spec_ref: journey-ux-ascii.md
- ui_shell_snapshot_ref: ui-shell-spec.md

## Page Goal
冻结 runner 的 CLI 控制面，让启动、claim、run、complete、fail 等动作形成可设计、可审计的用户操作边界。

## Main Path
- 进入 Runner 控制面流
- 查看首屏说明
- 执行核心输入或选择
- 点击主按钮
- 接收校验与提交反馈
- 进入下一步或完成本页

## Branch Paths
- Branch A: 点击主按钮 / 校验失败 / 修正信息 / 重新提交
- Branch B: 提交请求 / 服务端失败 / 展示错误 / 允许重试

## States
- initial: 展示默认结构与说明
- ready: 页面主要结构和主操作已就绪
- partial: 展示局部状态和骨架
- retryable_error: 展示错误并保留上下文
- settled: 展示最终结构

## Actions
- 继续 (primary)
- 重置场景 (reset)

### FEAT-SRC-003-007 · UI Spec Bundle for FEAT-SRC-003-007
- source_package_ref: artifacts/proto-to-ui/src003-adr042-ui-007-20260407-r1--feat-src-003-007
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-007
- ui_action: update

#### UI Spec runner-运行监控流

# UI Spec runner-运行监控流

- feat_ref: FEAT-SRC-003-007
- page_title: Runner 运行监控流
- journey_structural_spec_ref: journey-ux-ascii.md
- ui_shell_snapshot_ref: ui-shell-spec.md

## Page Goal
冻结 runner 的观察面，让 ready backlog、running、failed、deadletters 与 waiting-human 成为用户可见的正式产品面。

## Main Path
- 进入 Runner 运行监控流
- 查看首屏说明
- 执行核心输入或选择
- 点击主按钮
- 接收校验与提交反馈
- 进入下一步或完成本页

## Branch Paths
- Branch A: 点击主按钮 / 校验失败 / 修正信息 / 重新提交
- Branch B: 提交请求 / 服务端失败 / 展示错误 / 允许重试

## States
- initial: 展示默认结构与说明
- ready: 页面主要结构和主操作已就绪
- partial: 展示局部状态和骨架
- retryable_error: 展示错误并保留上下文
- settled: 展示最终结构

## Actions
- 继续 (primary)
- 重置场景 (reset)
