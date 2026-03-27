---
id: SRC-003
ssot_type: SRC
title: ADR 018 Execution Loop Job Runner 作为自动推进运行时
status: frozen
version: v1
schema_version: 1.0.0
src_root_id: src-root-src-003
workflow_key: product.raw-to-src
workflow_run_id: adr018-raw2src-restart-20260326-r1
source_kind: governance_bridge_src
source_refs:
- ADR-018
- ADR-020
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
candidate_package_ref: artifacts/raw-to-src/adr018-raw2src-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T09:21:36Z'
---

# ADR 018 Execution Loop Job Runner 作为自动推进运行时

## 问题陈述

LL 已经具备 `submit-handoff -> decide -> materialize -> dispatch -> close-run` 的 gate 主链，也已经能在 gate 批准后生成结构化 ready job。缺口在于系统此前没有正式 consumer 去消费 `artifacts/jobs/ready/` 中的 job，并把它推进到下游 workflow。

如果继续依赖“第三会话人工接力”，双会话双队列只会停留在架构口号，`dispatch` 也会退化成“写一份待办说明”。因此，SRC-003 把 ADR-018 收敛为一条明确的主链事实：

- gate approve 必须先确定 post-approve progression policy，再生成 ready 或 hold dispatch result；
- Execution Loop Job Runner 必须消费 ready job；
- 下游 workflow 必须通过结构化输入引用被自动拉起，而不是由额外会话猜路径接力。

## 目标用户

- 受该治理规则约束的 skill 作者
- workflow / orchestration 设计者
- human gate / reviewer
- artifact 管理与治理消费者

## 触发场景

- gate 批准某一正式产物并允许自动推进时。
- operator 需要用统一 CLI 启动、恢复或观察 execution loop 时。
- 下游 workflow 需要继承同一组 job schema、状态机与 evidence 约束时。

## 业务动因

- 必须把“dispatch 之后谁来跑”从隐式人工动作提升为正式运行时职责。
- 必须让下游围绕同一份 ready-job contract、状态机和 control surface 继承，而不是各自重写 runner 语义。
- 必须让 reviewer、operator 和下游 skill 在不回读原始 ADR 的前提下理解可执行边界。

## 语义清单

- Actors: 受该治理规则约束的 skill 作者; workflow / orchestration 设计者; human gate / reviewer; artifact 管理与治理消费者
- Product surfaces: ready job schema; execution runner state machine; workflow dispatch contract; execution evidence writeback policy
- Operator surfaces: canonical governed skill bundle `skills/l3/ll-execution-loop-job-runner/`; ll loop run-execution; ll loop resume-execution; ll loop show-status; ll loop show-backlog; ll job claim; ll job run; ll job complete; ll job fail
- Entry points: canonical governed skill bundle `skills/l3/ll-execution-loop-job-runner/`; ll loop run-execution; ll loop resume-execution
- Commands: ll loop run-execution; ll loop resume-execution; ll loop show-status; ll loop show-backlog; ll job claim; ll job run; ll job complete; ll job fail
- Runtime objects: ready execution job; claimed execution job; execution attempt evidence; workflow invocation result; runner status snapshot
- States: ready; claimed; running; done; failed; waiting-human; deadletter
- Observability surfaces: runner status snapshot; ready backlog; running jobs; failed jobs; waiting-human jobs; deadletters

## 统一 contract

下游继承时必须把以下字段视为 ready-job 的最小正式 contract：

- `job_id`
- `job_type`
- `status`
- `queue_path`
- `target_skill`
- `progression_mode`
- `source_run_id`
- `gate_decision_ref`
- `input_refs`
- `authoritative_input_ref`
- `formal_ref` 或 `handoff_ref`
- `retry_count`
- `retry_budget`
- `created_at`

兼容字段 `source_artifacts` 可以保留，但只作为历史 writer/reader 的镜像视图，不得替代 `input_refs` 与 `authoritative_input_ref`。

其中 `progression_mode` 的最小词表冻结为：

- `auto-continue`: gate 允许自动推进，dispatch 可生成 `status=ready` 的 next-skill job
- `hold`: gate 批准当前对象，但下游推进必须停在 hold/waiting-human 边界，待环境、部署或人工前置满足后再释放

## 当前实现状态

截至 2026-03-27，本仓库已经落地以下最小主链：

- `ll gate dispatch` 生成结构化 downstream dispatch result，并同时写入 `input_refs`、`authoritative_input_ref`、`formal_ref` 等字段；其中 `status=ready` 只适用于 `progression_mode=auto-continue`。
- `ll loop run-execution` / `ll loop resume-execution` 可作为 execution runner 的 repo CLI control carrier，扫描 ready queue、claim job、执行下游 workflow、回写 `done/failed`。
- `ll job claim/run/complete/fail` 提供显式控制面，用于修复、人工介入和调试。
- runner 会写执行 attempt evidence，并生成 ready/running/failed/backlog 视图。
- 根据 ADR-020，用户可调用的 runner skill authority 不应再落成 repo CLI façade，而应落在 canonical governed skill bundle `skills/l3/ll-execution-loop-job-runner/`。

当前仍保留以下下一阶段工作：

- 强化 `retry-reentry`、`waiting-human`、`deadletter` 的策略与恢复流程；
- 扩大自动推进覆盖链路；
- 补齐 claim timeout / lease recovery 等单消费者之外的恢复协议。

## 标准化决策

- source_projection: 将原始输入统一映射为主链兼容的标准字段。 (loss_risk=low)
- bridge_projection: 为下游 workflow 提供兼容的 bridge projection，同时保留 high-fidelity source layer。 (loss_risk=medium)
- semantic_lock_freeze: 避免下游 workflow 继续从 generic bridge prose 推断主导语义。 (loss_risk=low)
- operator_surface_preservation: 避免 CLI/operator/control surface 在 SRC 层被静默压缩。 (loss_risk=low)

## 压缩与省略说明

- Compressed: problem_statement | why=正文会被整理为适合下游消费的规范化问题陈述。 | risk=low
- Compressed: bridge_context | why=bridge projection 会把 raw 中分散的治理语义压缩为统一继承视图。 | risk=medium
- Summary: SRC 同时保留 high-fidelity source layer 和 bridge projection；任何压缩都必须显式记录。

## Operator Surface Inventory

- skill_entry: canonical governed skill bundle `skills/l3/ll-execution-loop-job-runner/` | phase=start/resume | actor=workflow / orchestration operator
- cli_control_surface: ll loop run-execution | phase=start | actor=Claude/Codex CLI operator
- cli_control_surface: ll loop resume-execution | phase=resume | actor=Claude/Codex CLI operator
- cli_control_surface: ll loop show-status | phase=monitor | actor=Claude/Codex CLI operator
- cli_control_surface: ll loop show-backlog | phase=monitor | actor=Claude/Codex CLI operator
- cli_control_surface: ll job claim | phase=init | actor=Claude/Codex CLI operator
- cli_control_surface: ll job run | phase=run | actor=Claude/Codex CLI operator
- cli_control_surface: ll job complete | phase=repair | actor=Claude/Codex CLI operator
- cli_control_surface: ll job fail | phase=repair | actor=Claude/Codex CLI operator
- monitor_surface: runner observability surface | phase=monitor | actor=workflow / orchestration operator

## 用户入口与控制面

- 主入口 skill authority: `skills/l3/ll-execution-loop-job-runner/`
- installed adapter target: Claude/Codex runtime installed adapter for `ll-execution-loop-job-runner`
- CLI control surface carrier: ll loop run-execution; ll loop resume-execution; ll loop show-status; ll loop show-backlog; ll job claim; ll job run; ll job complete; ll job fail
- 运行监控面: runner observability surface
- 用户交互边界: 用户通过 Claude/Codex CLI 调用 installed runner skill adapter，或通过 repo CLI control command 启动、恢复、观察运行时；两者 authority 不得混层。

## 冲突与未决点

- 第三会话人工接力: rejected | ready-job emission 必须与 runner 自动消费绑定，不能继续作为正式执行形态保留。

## 目标能力对象

- execution runner 对应的正式对象、contract、state machine 与 control surface

## 成功结果

- skill author 不再自行定义等价治理对象或边界。
- reviewer 可在不回读原始 ADR 的前提下判断候选是否满足主要约束。
- 下游消费方可按统一 contract、boundary 与 lineage 读取正式对象。

## 治理变更摘要

- 治理对象：Execution Loop Job Runner 与 ready execution job contract
- 统一原则：gate approve、progression_mode、ready/hold dispatch、runner auto progression 必须被视为同一条治理闭环。
- 下游必须继承的约束：下游需求链不得回退为 formal publication 停止态，也不得重新引入第三会话人工接力；未获 `auto-continue` 的批准不得泄漏为 ready queue job。

## Semantic Lock

- domain_type: execution_runner_rule
- one_sentence_truth: gate approve 后必须先确定 progression_mode；只有 `auto-continue` 才能生成 ready execution job 并由 Execution Loop Job Runner 自动消费 artifacts/jobs/ready 推进到下一个 skill，`hold` 必须停在正式 hold 边界。
- primary_object: execution_loop_job_runner
- lifecycle_stage: post_gate_auto_progression
- allowed_capabilities: ready_execution_job_materialization; ready_queue_consumption; next_skill_dispatch; execution_result_recording; retry_reentry_return
- forbidden_capabilities: formal_publication_substitution; admission_only_decomposition; third_session_human_relay; directory_guessing_consumer
- inheritance_rule: approve semantics must stay coupled to progression_mode-controlled ready/hold dispatch and runner-driven next-skill progression; downstream may not replace this with formal publication, admission-only flows, or implicit auto-dispatch.

## 下游派生要求

- 围绕治理对象定义正式 contract、schema、policy 与 lifecycle。
- 把关键约束落成可校验的 validation、evidence 与 gate-ready 输出。
- 确保下游 EPIC / FEAT / TASK 不遗漏主要治理对象与继承边界。

## 关键约束

- runner 只能消费结构化 job object 与正式引用，不得扫描目录猜业务输入。
- gate 必须显式给出 `progression_mode`，不得把“是否自动推进”延迟到 runner 执行时猜测。
- ready job 的主输入必须通过 `input_refs` 与 `authoritative_input_ref` 明确给出。
- gate、formal publication、execution progression 三者边界必须分离，不得重新混层。

## 范围边界

- In scope: 定义 ready-job schema、runner state machine、operator surface 与 evidence writeback 的统一约束。
- In scope: 为后续主链对象提供统一交接依据，使 `dispatch -> run-execution -> outcome` 成为正式主链。
- Out of scope: 具体业务 skill 的内部实现细节。

## 来源追溯

- Source refs: ADR-018, ADR-020, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- Input type: adr

## 桥接摘要

- 本 SRC 的作用不是重复 ADR 论证，而是把治理结论转译成下游可直接继承的正式边界。
- 下游应默认继承这里定义的 ready-job contract、runner state machine 与 control surface，而不是重新发明等价规则。

## Bridge Context

- 结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。
- governed_by_adrs: ADR-018, ADR-020, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- change_scope: 将《ADR 018 Execution Loop Job Runner 作为自动推进运行时》收敛为 progression-mode-controlled ready/hold dispatch、runner auto progression 与 execution evidence 的统一主链边界。
- governance_objects: ready execution job contract; execution loop job runner; runner observability surface
- current_failure_modes: dispatch 只写 job 不消费; formal publication 后停滞; 第三会话人工接力; 目录猜测输入; 缺少统一 outcome writeback
- downstream_inheritance_requirements: 下游需求链必须继承 progression_mode、ready-job contract、runner state machine、CLI control surface 与 evidence writeback 约束。
- expected_downstream_objects: EPIC, FEAT, TASK
- acceptance_impact: 下游 gate、auditor 与 handoff 必须基于同一组 ready-job / runner contract 判断正式产物是否合法。; 下游消费方应能在不回读原始 ADR 的前提下理解谁发出了 ready job、谁 claim 了 job、谁执行了下一步 workflow。; 审计链应能回答 job 从 ready 到 outcome 的完整迁移。
- non_goals: 具体业务 skill 的内部实现细节。
