---
id: EPIC-002
ssot_type: EPIC
src_ref: SRC-ADR018-RAW2SRC-RESTART-20260326-R1
title: Gate 审批后自动推进 Execution Runner 统一能力
status: accepted
schema_version: 1.0.0
epic_root_id: EPIC-002
workflow_key: product.src-to-epic
workflow_run_id: adr018-src2epic-restart-20260326-r1
candidate_package_ref: artifacts/src-to-epic/adr018-src2epic-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
depends_on:
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- SRC-ADR018-RAW2SRC-RESTART-20260326-R1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
frozen_at: '2026-03-26T13:04:11Z'
acceptance_summary: Epic acceptance review passed.
---

# Gate 审批后自动推进 Execution Runner 统一能力

## Epic Intent

将《ADR 018 Execution Loop Job Runner 作为自动推进运行时》中的治理问题空间进一步收敛为“Gate 审批后自动推进 Execution Runner 统一能力”这一 EPIC 级产品能力块，让下游可以围绕稳定的产品行为切片拆分 FEAT，并把 capability axes 保留在 cross-cutting constraints 层，而不是继续复述 SRC 原则或沿治理对象逐项平移。

## Business Goal

本 EPIC 的核心不是把 approve 改写成 formal publication，而是把 gate 批准后的自动推进运行时冻结成连续产品行为。下游 FEAT 需要围绕 批准后 Ready Job 生成流、Runner 用户入口流、Runner 控制面流、Execution Runner 自动取件流 这些切片定义 approve 后的 ready job、runner 消费、next-skill dispatch 和 execution result 回写。

## Business Value and Problem

- 这导致系统虽然在架构目标上是“双会话双队列”，但实际运行上仍表现为： 当前执行链已经出现Execution Loop 消费自动执行队列、下游应消费结构化流转对象，而不是目录猜测、但当前仍缺少一个正式 consumer 去自动消费 artifacts/jobs/ready/ 中的 job，并把它推进到下游 workflow等失控行为。 这会直接造成但如果长期依赖“第三会话人工接力”，则三会话过渡形态会被误当成正式架构，导致 ADR-001 的目标无法收敛落地、无法形成统一 execution loop、dispatch 无法真正构成自动推进。 正式文件读写统一纳入围绕 双会话双队列闭环 的治理边界，不再依赖分散约定。
- 需要现在就把这类治理变化收敛成正式需求源，否则但如果长期依赖“第三会话人工接力”，则三会话过渡形态会被误当成正式架构，导致 ADR-001 的目标无法收敛落地、无法形成统一 execution loop会继续沿后续需求链扩散。
- 关键触发场景：当治理类变更需要被下游 skill 继承时。

## Product Positioning

该 EPIC 位于 gate 后自动推进运行时层，承接上游 bridge SRC，对下定义一条从 approve 后 ready job 生成、runner 自动取件、next-skill dispatch 到 execution result 回写的完整产品线。它对外呈现的是 批准后 Ready Job 生成流、Runner 用户入口流、Runner 控制面流、Execution Runner 自动取件流、下游 Skill 自动派发流 这些可交付的自动推进产品流；批准后 Ready Job 生成能力、Runner 用户入口能力、Runner 控制面能力、Execution Runner 取件能力、下游 Skill 自动派发能力 只作为这些产品流共享的 cross-cutting constraints 存在。

## Actors and Roles

- gate / reviewer owner：定义 approve 与非 approve 决策何时产生 ready execution job。
- execution runner owner：负责 ready queue 消费、claim 语义、dispatch 与结果回写。
- downstream governed skill owner：消费 authoritative runner invocation，而不是等待人工接力。
- workflow / orchestration 设计者：保持 gate approve、job queue、runner 和 next skill 之间的单一路径。
- Claude/Codex CLI operator：通过 runner skill 入口和 CLI control surface 启动、恢复、控制 execution loop。
- workflow / orchestration operator：通过 runner observability surface 观察 ready backlog、running、failed、deadletters 与 waiting-human 状态。

## Capability Scope

- 统一上位产品能力：形成一条 gate approve 后自动推进到下一 skill 的运行时产品线。
- 产品行为切片：批准后 Ready Job 生成流，对业务方交付 给 Execution Loop Job Runner 消费的 ready execution job，以及可追溯的 approve-to-job 关系。
- 产品行为切片：Runner 用户入口流，对业务方交付 给 Claude/Codex CLI operator 使用的 runner skill entry 与启动记录。
- 产品行为切片：Runner 控制面流，对业务方交付 给 Claude/Codex CLI operator 使用的 runner control surface 与结构化执行状态。
- 产品行为切片：Execution Runner 自动取件流，对业务方交付 给编排方使用的 claimed execution job / running record，以及可追溯的 claim 证据。
- 产品行为切片：下游 Skill 自动派发流，对业务方交付 给下游 governed skill 使用的 authoritative invocation，以及给运行时使用的 execution attempt record。
- 产品行为切片：执行结果回写与重试边界流，对业务方交付 给编排方和审计链使用的 execution outcome、retry / reentry directive 与失败证据。
- 产品行为切片：Runner 运行监控流，对业务方交付 给 workflow / orchestration operator 使用的 runner observability surface 与运行态视图。
- Cross-cutting capability constraints：批准后 Ready Job 生成能力、Runner 用户入口能力、Runner 控制面能力、Execution Runner 取件能力、下游 Skill 自动派发能力、执行结果回写与重试边界能力、Runner 监控与观察能力；这些能力轴只作为约束附着在上述产品行为切片上。

## Upstream and Downstream

- Upstream：承接 `product.raw-to-src::adr018-raw2src-restart-20260326-r1` 冻结后的 SRC 包，而不是原始需求或单个 ADR 原文。
- Downstream：产出一个可继续拆分为多个 FEAT 的单一主 EPIC，并交接给 `product.epic-to-feat`。
- 上游输入形态：关于 gate approve 后自动推进缺口的 bridge SRC，而不是 formal publication/admission 产品线定义。
- 下游消费形态：ready job emission、runner intake、next-skill dispatch、execution result feedback 等自动推进 FEAT 切片。

## Epic Success Criteria

- 下游 FEAT 能完整覆盖 批准后 Ready Job 生成流、Runner 用户入口流、Runner 控制面流、Execution Runner 自动取件流 这些自动推进产品切片，而不是把 approve 后流程改写成 formal publication / admission。
- 至少一条 gate approve -> ready execution job -> runner claim -> next skill invocation 的真实链路可被验证。
- ready queue、runner ownership、next-skill dispatch 与 execution outcome 的职责边界不再依赖人工接力。
- 失败、重试和回流仍保持 execution 语义，而不是在 approve 之后丢失运行时状态。

## Non-Goals

- 本 EPIC 不负责下游 EPIC/FEAT/TASK 分解与实现细节。
- 本 EPIC 不把 approve 重写成 formal publication、admission 或 publish-only 终态。
- 本 EPIC 不要求第三会话人工接力作为正常自动推进路径。
- 本 EPIC 不扩张成重型调度平台、事件总线或仓库级通用执行器设计。
- 本 EPIC 不把 runner intake 替换成目录扫描、路径猜测或临时脚本调用。

## Decomposition Rules

- 按独立验收的产品行为切片拆分 FEAT，不按实现顺序、能力轴名称或单一任务切分。
- 每个下游 FEAT 都必须继承 src_root_id、epic_freeze_ref 和 authoritative source_refs。
- FEAT 的 primary decomposition unit 是 approve 后 ready job 生成、runner intake、next-skill dispatch 与 execution result feedback 这些自动推进切片。
- 任何 FEAT 都不得把 approve 后链路重写成 formal publication、admission 或人工第三会话接力。
- 下游 FEAT 必须保持 artifacts/jobs/ready、runner claim 和 next-skill invocation 之间的单一路径。
- 失败、重试和回流必须保持 execution 语义，不得在 FEAT 层改写为 publish-only 状态。
- 建议产品行为切片：
  - 批准后 Ready Job 生成流 <- 批准后 Ready Job 生成能力
  - Runner 用户入口流 <- Runner 用户入口能力
  - Runner 控制面流 <- Runner 控制面能力
  - Execution Runner 自动取件流 <- Execution Runner 取件能力
  - 下游 Skill 自动派发流 <- 下游 Skill 自动派发能力
  - 执行结果回写与重试边界流 <- 执行结果回写与重试边界能力
  - Runner 运行监控流 <- Runner 监控与观察能力

## Rollout and Adoption

- rollout_required: `true`
- trigger_score: `4`
- SRC 涉及共享治理底座或共用运行时能力，而不是单一业务功能。
- 功能真正生效依赖现有 skill / workflow 接入，而不是只完成底座建设。
- 效果判定依赖真实 producer / consumer 接入，不能只靠组件内自测证明。
- 需要跨 skill E2E 或 handoff/gate 闭环验证，才能证明治理主链真的成立。
- required_feat_tracks: `foundation, adoption_e2e`
- rollout / adoption / E2E 不另起第二个 EPIC，而是在当前主 EPIC 内显式保留，并在 epic-to-feat 阶段强制拆出独立 FEAT 族。
- foundation FEAT 与 adoption/E2E FEAT 必须共享同一组 source_refs 和治理约束，不得形成并行真相。
- default-active 与 guarded/provisional 切面必须分层表达，避免未冻结 slice 被误当成已默认启用能力。
- required_feat_families:
  - skill_onboarding: 建立现有 governed skill 的 integration matrix，明确 producer、consumer、gate consumer 与暂不接入对象。
  - migration_cutover: 定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，而不是一次性全仓硬切。
  - cross_skill_e2e_validation: 至少选定一条真实 producer -> consumer -> audit -> gate 的 pilot 主链，并形成跨 skill E2E evidence。

## Constraints and Dependencies

### Epic-level constraints

- 本 EPIC 直接负责 gate approve 后的自动推进运行时，不把 approve 停在 formal publication 或人工接力。
- 自动推进主链固定为：approve -> ready execution job -> runner claim -> next skill dispatch -> execution outcome。
- artifacts/jobs/ready 是正式 ready queue；runner claim 是唯一 intake；next skill dispatch 必须保留 authoritative refs 和目标 skill 边界。

### Authoritative inherited constraints

- Semantic lock truth: gate approve 后必须生成 ready execution job，并由 Execution Loop Job Runner 自动消费 artifacts/jobs/ready 后推进到下一个 skill，而不是停在 formal publication 或人工接力。
- Allowed capabilities: ready_execution_job_materialization, ready_queue_consumption, next_skill_dispatch, execution_result_recording, retry_reentry_return
- Forbidden capabilities: formal_publication_substitution, admission_only_decomposition, third_session_human_relay, directory_guessing_consumer
- 正式文件读写必须围绕 双会话双队列闭环 的统一边界建模，不得在下游恢复自由路径写入。
- 下游需求链必须将 双会话双队列闭环 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。
- Authoritative source refs: ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- Upstream package: E:\ai\LEE-Lite-skill-first\artifacts\raw-to-src\adr018-raw2src-restart-20260326-r1

### Downstream preservation rules

- 下游 FEAT 不得把 automatic progression 重新解释成 formal publication / admission-only 链。
- 下游 FEAT 不得跳过 ready queue 和 runner claim 直接以人工接力或路径猜测触发下一个 skill。
- 执行结果、重试和失败证据必须继续保持 execution 语义可追溯。

## Acceptance and Review

- Upstream acceptance: approve (Acceptance review passed.)
- Upstream semantic review: pass (No semantic issue detected.)
- Epic review: pass
- Epic acceptance: approve

## Downstream Handoff

- Next workflow: `product.epic-to-feat`
- epic_freeze_ref: `EPIC-GATE-EXECUTION-RUNNER`
- src_root_id: `SRC-ADR018-RAW2SRC-RESTART-20260326-R1`
- Required carry-over: source refs, decomposition rules, constraints, acceptance evidence

## Traceability

- Epic Intent: problem_statement, trigger_scenarios, business_drivers <- ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- Business Value and Problem: problem_statement, business_drivers, trigger_scenarios <- ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- Actors and Roles: target_users, trigger_scenarios, bridge_context.downstream_inheritance_requirements <- SRC-ADR018-RAW2SRC-RESTART-20260326-R1, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- Capability Scope: in_scope, governance_change_summary, bridge_context.governance_objects <- SRC-ADR018-RAW2SRC-RESTART-20260326-R1, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- Constraints and Dependencies: key_constraints, bridge_context.downstream_inheritance_requirements <- product.raw-to-src::adr018-raw2src-restart-20260326-r1, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
- Epic Success Criteria: business_drivers, bridge_context.acceptance_impact, trigger_scenarios <- product.raw-to-src::adr018-raw2src-restart-20260326-r1, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009
