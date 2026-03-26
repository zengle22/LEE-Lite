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

这导致系统虽然在架构目标上是“双会话双队列”，但实际运行上仍表现为： 当前执行链已经出现Execution Loop 消费自动执行队列、下游应消费结构化流转对象，而不是目录猜测、但当前仍缺少一个正式 consumer 去自动消费 artifacts/jobs/ready/ 中的 job，并把它推进到下游 workflow等失控行为。 这会直接造成但如果长期依赖“第三会话人工接力”，则三会话过渡形态会被误当成正式架构，导致 ADR-001 的目标无法收敛落地、无法形成统一 execution loop、dispatch 无法真正构成自动推进。 正式文件读写统一纳入围绕 双会话双队列闭环 的治理边界，不再依赖分散约定。

## 目标用户

- 受该治理规则约束的 skill 作者
- workflow / orchestration 设计者
- human gate / reviewer
- artifact 管理与治理消费者

## 触发场景

- 当治理类变更需要被下游 skill 继承时。

## 业务动因

- 需要现在就把这类治理变化收敛成正式需求源，否则但如果长期依赖“第三会话人工接力”，则三会话过渡形态会被误当成正式架构，导致 ADR-001 的目标无法收敛落地、无法形成统一 execution loop会继续沿后续需求链扩散。
- 将 ADR 归一为 bridge SRC 的价值，是让下游围绕 双会话双队列闭环 共享同一组继承约束，而不是继续各自猜路径或重写规则。
- 这能为后续链路提供稳定输入：下游需求链必须将 双会话双队列闭环 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## 语义清单

- Actors: 受该治理规则约束的 skill 作者; workflow / orchestration 设计者; human gate / reviewer; artifact 管理与治理消费者
- Product surfaces: 双会话双队列闭环 对应的正式对象、contract 或 policy; skill author 不再自行定义等价治理对象或边界。; reviewer 可在不回读原始 ADR 的前提下判断候选是否满足主要约束。; 下游消费方可按统一 contract、boundary 与 lineage 读取正式对象。
- Operator surfaces: Execution Loop Job Runner; ll loop run-execution; ll job claim; ll job run; ll job complete; ll job fail; runner observability surface
- Entry points: Execution Loop Job Runner; ll loop run-execution; ll job claim; ll job run; ll job complete; ll job fail
- Commands: ll loop run-execution; ll job claim; ll job run; ll job complete; ll job fail
- Runtime objects: ready_execution_job_materialization; ready_queue_consumption; next_skill_dispatch; execution_result_recording; retry_reentry_return; ready execution job; claimed execution job; next-skill invocation; execution outcome
- States: * 上游 workflow 可以产出 freeze-ready package；; 但当前仍缺少一个正式 consumer 去自动消费 `artifacts/jobs/ready/` 中的 job，并把它推进到下游 workflow。; * 自动消费 ready job 的 execution runner; * 谁来把 ready job claim 成 running；; * 谁来把执行结果回写为 `done / failed / waiting-human / deadletter`；; 如果 ready job 不被正式 consumer 消费，那么：; * `jobs/ready/`; * `jobs/running/`
- Observability surfaces: runner observability surface; * ready backlog; * running jobs; * failed jobs; * deadletters; * waiting-human jobs

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

- skill_entry: Execution Loop Job Runner | phase=start | actor=workflow / orchestration operator
- cli_control_surface: ll loop run-execution | phase=start | actor=Claude/Codex CLI operator
- cli_control_surface: ll job claim | phase=init | actor=Claude/Codex CLI operator
- cli_control_surface: ll job run | phase=run | actor=Claude/Codex CLI operator
- cli_control_surface: ll job complete | phase=repair | actor=Claude/Codex CLI operator
- cli_control_surface: ll job fail | phase=repair | actor=Claude/Codex CLI operator
- monitor_surface: runner observability surface | phase=monitor | actor=workflow / orchestration operator

## 用户入口与控制面

- 主入口 skill: Execution Loop Job Runner
- CLI control surface: ll loop run-execution; ll job claim; ll job run; ll job complete; ll job fail
- 运行监控面: runner observability surface
- 用户交互边界: 用户通过 Claude/Codex CLI 显式调用 skill 入口或控制命令启动、恢复、观察运行时。

## 冲突与未决点

- 第三会话: unresolved | requires_human_confirmation=True

## 目标能力对象

- 双会话双队列闭环 对应的正式对象、contract 或 policy

## 成功结果

- skill author 不再自行定义等价治理对象或边界。
- reviewer 可在不回读原始 ADR 的前提下判断候选是否满足主要约束。
- 下游消费方可按统一 contract、boundary 与 lineage 读取正式对象。

## 治理变更摘要

- 治理对象：双会话双队列闭环
- 统一原则：正式文件读写统一纳入围绕 双会话双队列闭环 的治理边界，不再依赖分散约定。
- 下游必须继承的约束：下游需求链必须将 双会话双队列闭环 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## Semantic Lock

- domain_type: execution_runner_rule
- one_sentence_truth: gate approve 后必须生成 ready execution job，并由 Execution Loop Job Runner 自动消费 artifacts/jobs/ready 后推进到下一个 skill，而不是停在 formal publication 或人工接力。
- primary_object: execution_loop_job_runner
- lifecycle_stage: post_gate_auto_progression
- allowed_capabilities: ready_execution_job_materialization; ready_queue_consumption; next_skill_dispatch; execution_result_recording; retry_reentry_return
- forbidden_capabilities: formal_publication_substitution; admission_only_decomposition; third_session_human_relay; directory_guessing_consumer
- inheritance_rule: approve semantics must stay coupled to ready-job emission and runner-driven next-skill progression; downstream may not replace this with formal publication or admission-only flows.

## 下游派生要求

- 围绕治理对象定义正式 contract、schema、policy 与 lifecycle。
- 把关键约束落成可校验的 validation、evidence 与 gate-ready 输出。
- 确保下游 EPIC / FEAT / TASK 不遗漏主要治理对象与继承边界。

## 关键约束

- 正式文件读写必须围绕 双会话双队列闭环 的统一边界建模，不得在下游恢复自由路径写入。
- 下游需求链必须将 双会话双队列闭环 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## 范围边界

- In scope: 定义 skill 文件读写、artifact 输入输出边界与路径策略的统一治理边界。
- In scope: 为后续主链对象提供统一约束来源与交接依据，而不是在本层展开 API 或实现设计。
- Out of scope: 下游 EPIC/FEAT/TASK 分解与实现细节。

## 来源追溯

- Source refs: ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- Input type: adr

## 桥接摘要

- 本 SRC 的作用不是重复 ADR 论证，而是把治理结论转译成下游可直接继承的正式边界。
- 下游应默认继承这里定义的治理对象、约束和交接边界，而不是重新发明等价规则。

## Bridge Context

- 结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。
- governed_by_adrs: ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- change_scope: 将《ADR 018 Execution Loop Job Runner 作为自动推进运行时》涉及的双会话双队列闭环收敛为统一主链继承边界，明确 loop、handoff、gate 与 formal materialization 的协作责任。
- governance_objects: 双会话双队列闭环
- current_failure_modes: Execution Loop 消费自动执行队列；; 下游应消费结构化流转对象，而不是目录猜测。; 但当前仍缺少一个正式 consumer 去自动消费 artifacts/jobs/ready/ 中的 job，并把它推进到下游 workflow。
- downstream_inheritance_requirements: 下游需求链必须将 双会话双队列闭环 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。
- expected_downstream_objects: EPIC, FEAT, TASK
- acceptance_impact: 下游 gate、auditor 与 handoff 必须基于同一组受治理边界判断正式产物是否合法。; 下游消费方应能在不回读原始 ADR 的前提下理解主要失控行为与统一治理理由。; 审计链应能回答谁推进了 candidate、谁做了 final decision、为什么允许推进、正式物化了什么对象。
- non_goals: 下游 EPIC/FEAT/TASK 分解与实现细节。
