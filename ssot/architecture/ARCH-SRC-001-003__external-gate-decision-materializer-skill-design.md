---
id: ARCH-SRC-001-003
ssot_type: ARCHITECTURE
title: External Gate Decision Materializer Skill Design
status: active
lifecycle_state: historical_only
higher_order_status: superseded
superseded_by:
  - ADR-016
version: v1
schema_version: 0.1.0
architecture_root_id: arch-root-src-001-003
parent_id: SRC-001
derived_from_ids:
  - id: SRC-001
    version: v1
    required: true
  - id: ARCH-SRC-001-001
    version: v3
    required: true
  - id: ARCH-SRC-001-002
    version: v1
    required: true
source_refs:
  - SRC-001
  - EPIC-SRC-001-001
  - FEAT-SRC-001-001
  - FEAT-SRC-001-002
  - FEAT-SRC-001-003
  - FEAT-SRC-001-004
  - FEAT-SRC-001-005
  - TECH-SRC-001-001
  - TECH-SRC-001-002
  - TECH-SRC-001-003
  - ADR-001
  - ADR-003
  - ADR-005
  - ADR-006
  - ADR-009
owner: system-architecture-owner
tags: [architecture, external-gate, decision, materialization, ssot, skill, cli]
workflow_key: manual.architecture.component
workflow_instance_id: manual-architecture-src-001-external-gate-20260325
properties:
  src_root_id: src-root-src-001
  component_type: governed skill
  runtime_carrier: cli-first file-runtime
  standard_skill_name: ll-gate-decision-materializer
  precedence_rule: if this design conflicts with ADR-006 or ARCH-SRC-001-002, ADR-006 and ARCH-SRC-001-002 win
historical_note: This architecture note preserves the pre-ADR-016 external gate materializer design. Current gate runtime identity and second-session queue semantics are governed by ADR-016 and ll-gate-human-orchestrator.
---

# External Gate Decision Materializer Skill Design

> 历史说明：本文保留 external gate 分层、formal object 只能经 gate 晋升、formal 写入必须走受治理 IO 这些设计动机。
>
> 对当前实现，`ADR-016` 的 `ll-gate-human-orchestrator`、pending gate queue、claim / decision / dispatch 接缝优先于本文中的 materializer 命名和对象名。

## 文档定位

本文档把 `ADR-006` 已冻结的 External Gate 原则收成一份可实施的组件设计，回答：

- `ll-gate-decision-materializer` 到底是什么组件
- 它的输入、输出、状态和流程是什么
- 它和 workflow skill、formal SSOT、human loop、consumer 的边界是什么
- 它在正式物化 `ssot/*` 时必须遵守哪些集成纪律

若与 [ADR-006](E:/ai/LEE-Lite-skill-first/ssot/adr/ADR-006-External%20Gate%20独立%20Skill%20化的%20Decision%20与%20Materialization%20层.MD) 或 [ARCH-SRC-001-002__governed-skill-candidate-and-gate-materialization-integration.md](E:/ai/LEE-Lite-skill-first/ssot/architecture/ARCH-SRC-001-002__governed-skill-candidate-and-gate-materialization-integration.md) 冲突，以前两者为准。

## 核心结论

`ll-gate-decision-materializer` 是一类独立 governed skill / gate loop consumer，不是业务 skill 的附属脚本。

它固定承担五类职责：

- decision
- formal object materialization
- materialized handoff
- materialized job
- run closure

它不负责：

- 重写上游 candidate 内容
- 重新做一遍业务语义设计
- 让 business skill 直接写正式 `ssot/*`
- 绕过受治理 IO / Registry / Path Policy 直接落正式对象

## 组件边界

### 上游输入

External Gate 至少消费以下对象：

- `candidate package`
- `proposal`
- `review / acceptance evidence`
- `audit finding mapping`
- `run state`
- `retry budget`
- `gate-ready package`

### 下游输出

External Gate 至少产出以下对象：

- `gate-decision.json`
- `materialized-ssot.json` 或等价 formal object receipt
- `materialized-handoff.json`
- `materialized-job.json`
- `run-closure.json`
- formal `ssot/*`

### 权威边界

- business skill 只负责 `candidate package / proposal / evidence`
- gate 是唯一 formal `ssot/*` 写入入口
- consumer 只能消费 formal object / formal ref，不能把 candidate 当正式输入

## 组件结构

```text
[Workflow Skill]
      |
      v
[Managed Candidate Package] --> [External Gate Reader] --> [Decision Engine] --> [Decision Object]
                                                                   |                  |
                                                                   |                  +--> [Run Closure Writer]
                                                                   |
                                                                   +--> revise/retry --> [Runtime Re-entry Writer]
                                                                   +--> handoff       --> [Handoff Materializer]
                                                                   +--> approve       --> [Formal Materializer] --> [Registry / Lineage] --> [Formal SSOT]
                                                                   +--> reject        --> [Run Closure Writer]
```

## 内部模块

推荐最小模块拆分如下：

- `cli/lib/gate_reader.py`
  - 读取 `gate-ready package`
  - 校验 completeness、run state、budget、evidence
- `cli/lib/gate_decision.py`
  - 执行 `approve / revise / retry / handoff / reject`
  - 生成唯一 `decision object`
- `cli/lib/gate_materializer.py`
  - 执行 formal object materialization
  - 执行 handoff/job materialization
- `cli/lib/gate_closure.py`
  - 写 `run-closure.json`
  - 结案原 run
- `cli/lib/gate_protocol.py`
  - 定义 `GateReadyPackage`、`GateDecision`、`FormalMaterializationRequest`、`RunClosure`
- `cli/commands/gate/command.py`
  - 暴露 `lee gate decide`
- `cli/commands/registry/command.py`
  - 暴露 `lee registry publish-formal`

## 决策模型

### 唯一合法词表

- `approve`
- `revise`
- `retry`
- `handoff`
- `reject`

### 语义约束

- 每次 gate 消费必须产出唯一 decision
- 不允许并列 approve/retry
- `revise` 与 `retry` 必须回到 runtime，且创建新 run
- `handoff` 必须物化 `materialized-handoff.json` 和 delegated human/special job
- `approve` 才允许进入 formal publish
- `reject` 终止推进并 closure

## 主流程

### 1. Gate Ready Intake

1. 读取 `gate-ready package`
2. 校验 candidate、proposal、evidence、run state 是否完整
3. 校验 package 是否满足进入 gate 的前置条件

### 2. Decision

1. 读取 `handoff_ref / proposal_ref`
2. 生成唯一 `decision object`
3. 写入 `gate-decision.json`
4. 写 decision evidence

### 3. Decision Branch

- `revise / retry`
  - 写 runtime re-entry
  - 原 run 结案
- `handoff`
  - 物化 `materialized-handoff.json`
  - 物化 delegated human-review / special-consumer job
  - 原 run 结案
- `approve`
  - 进入 formal materialization
- `reject`
  - 原 run 结案

### 4. Formal Materialization

1. 读取 `decision object`
2. 组装 `FormalMaterializationRequest`
3. 调受治理写入链路
4. 生成 formal object
5. 绑定 formal ref / lineage
6. 写 formal `ssot/*`
7. 写 `materialized-ssot.json`

### 5. Run Closure

1. 记录 decision summary
2. 记录 materialized refs
3. 写 `run-closure.json`
4. 将原 run 移入终态

## 正式物化约束

External Gate 在物化正式 `ssot/*` 时，必须遵守 [ARCH-SRC-001-002__governed-skill-candidate-and-gate-materialization-integration.md](E:/ai/LEE-Lite-skill-first/ssot/architecture/ARCH-SRC-001-002__governed-skill-candidate-and-gate-materialization-integration.md)。

这意味着：

- skill 侧只能写 `managed candidate`
- gate 侧才能写 formal `ssot/*`
- 必须走 `gate-ready package -> decision -> formal materialization -> ssot`
- 不允许 workflow skill 直接写 `ssot/src`、`ssot/epic`、`ssot/feat`、`ssot/tech`
- 不允许 gate 跳过 decision 直接 formalize

### 与 ADR-005 / ADR-009 的接缝

formal materialization 进入正式链路时必须走统一治理基础：

- `Gateway`
- `Path Policy`
- `Registry`
- `receipt`
- `registry_record_ref`

也就是说，Gate 不得自由直写正式文件系统；正式物化必须同时留下：

- `canonical_path`
- `receipt_ref`
- `registry_record_ref`

## CLI 接口

### `lee gate decide`

输入：

- `handoff_ref`
- `proposal_ref`
- `decision`
- `decision_reason`
- `review_context_ref`

输出：

- `decision_ref`
- `decision`
- `reentry_allowed`
- `materialization_required`
- `evidence_ref`

错误：

- `handoff_missing`
- `invalid_state`
- `decision_conflict`

### `lee registry publish-formal`

输入：

- `candidate_ref`
- `decision_ref`
- `target_kind`
- `publish_mode`

输出：

- `formal_ref`
- `lineage_ref`
- `publish_status`
- `receipt_ref`

错误：

- `decision_not_approvable`
- `registry_bind_failed`
- `publish_failed`

## 状态模型

### Gate 视角

- `gate_pending`
- `decision_issued`
- `reentry_pending`
- `handoff_pending`
- `materialization_pending`
- `publish_pending`
- `closed`

### 转移规则

- `gate_pending -> decision_issued`
- `decision_issued(revise/retry) -> reentry_pending -> closed`
- `decision_issued(handoff) -> handoff_pending -> closed`
- `decision_issued(approve) -> materialization_pending -> publish_pending|closed`
- `decision_issued(reject) -> closed`

## 异常与补偿

### decision 已落盘，但 formal materialization 失败

- 保留 `decision_ref`
- 状态进入 `materialization_pending`
- 禁止伪造 `formal_ref`

### formal object 已生成，但 registry bind 失败

- 回滚 formal publish 指针
- 保留 candidate 原状
- 进入 repair / manual retry

### formal object 已发布，但 downstream publish 失败

- 允许 partial success
- formal object 保持已物化
- 写 `publish_pending`
- 阻止 consumer admission

### human review timeout

- 只能输出显式 `handoff` 或 `retry`
- 不允许无证据自动 approve

## 与其他组件的挂接

### 与 workflow skill

- workflow skill 只负责生成 candidate side 内容
- gate 只消费 `gate-ready package`
- 两者通过文件对象协作，不直接相互调用

### 与 human loop

- human loop 不是 gate 本体
- gate 只负责在需要人工时物化 `materialized-handoff.json` 和 human-review job

### 与 consumer admission

- gate 负责把 candidate 晋升为 formal object
- admission checker 负责 consumer 是否可读
- gate 不直接代替 admission

## 明确禁止

- business skill 内嵌最终 gate decision
- business skill 内嵌 formal SSOT write
- gate 不经过 decision 直接 publish-formal
- gate 直接改写 candidate 本体并冒充原候选输出
- consumer 读取 `artifacts/<workflow>/<run_id>` 下 candidate 作为 formal input

## 开发建议

实现顺序建议固定为：

1. `gate-decide`
2. `decision evidence`
3. `reentry / handoff branch`
4. `publish-formal`
5. `run-closure`

不要先做：

- 多种 materializer 并行扩散
- 自定义旁路审批脚本
- 跳过 registry / lineage 的直接 formal 写盘

## 当前开工判定

按当前 `ADR-006 + ARCH-SRC-001-002 + rerun13 TECH`，External Gate 已达到可实施状态。

但开发时应把它视为一个集中实现组件，而不是把 decision、formalization、closure 分散给多个业务 skill 各自实现。
