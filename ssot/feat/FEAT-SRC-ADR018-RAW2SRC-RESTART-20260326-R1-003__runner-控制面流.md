---
id: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-003
ssot_type: FEAT
feat_ref: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-003
epic_ref: EPIC-GATE-EXECUTION-RUNNER
title: Runner 控制面流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr018-epic2feat-restart-20260326-r1
candidate_package_ref: artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T12:42:30Z'
---

# Runner 控制面流

## Goal
冻结 runner 的 CLI 控制面，让启动、claim、run、complete、fail 等动作形成可设计、可审计的用户操作边界。

## Scope
- 定义 CLI control surface：ll loop run-execution、ll job claim、ll job run、ll job complete、ll job fail。
- 定义各控制命令与 runner lifecycle / job lifecycle 的映射关系。
- 定义控制面输出的结构化状态，而不是把操作结果留成隐式终端副作用。

## Constraints
- runner control surface 必须提供统一的 CLI verbs，而不是分散在多个无治理脚本里。
- control surface 必须与 runner skill entry 对齐，不能绕开 authoritative run context。
- control verbs 不得直接替代 next-skill invocation 结果或篡改 execution outcome。
- 控制动作必须产生可追踪的 command / state evidence。

## Acceptance Checks
1. CLI controls are explicit
   Then: start, claim, run, complete, fail or equivalent control commands must be explicit and stable.
2. Control results are structured
   Then: the control surface must emit structured execution state rather than relying on ambiguous ad hoc logs.
3. Runner control verbs are unified
   Then: The FEAT must define one unified runner CLI control surface instead of scattering control verbs across ad-hoc scripts or undocumented commands.
