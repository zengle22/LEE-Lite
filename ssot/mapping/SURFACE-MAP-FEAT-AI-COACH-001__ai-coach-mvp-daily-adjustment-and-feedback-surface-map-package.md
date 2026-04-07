---
id: SURFACE-MAP-FEAT-AI-COACH-001
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-AI-COACH-001
feat_ref: FEAT-AI-COACH-001
title: AI Coach MVP 每日调整与训练后反馈 Surface Map
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-surface-map
workflow_run_id: example-ai-coach-mvp-surface-map
design_impact_required: true
owner_binding_status: bound
related_owner_refs:
  - ARCH-COACH-MVP-CORE
  - API-TRAINING-PLAN
  - UI-COACH-CONVERSATION-SHELL
  - PROTO-MVP-COACH-MAIN
  - TECH-PLAN-ADJUSTMENT
source_refs:
  - FEAT-AI-COACH-001
  - EPIC-AI-COACH-MVP
  - SRC-AI-COACH-MVP
  - ADR-040
  - ADR-041
  - ADR-042
---

# Surface Map Package for AI Coach MVP 每日调整与训练后反馈

> 这是一份示例型 `surface_map_package`。
> 目的不是新建一套与 FEAT 一对一绑定的设计资产，而是展示：
> 同一个 AI 教练 MVP FEAT 如何受控更新既有 shared design assets。

## Package Semantics

- artifact_type: `surface_map_package`
- workflow_key: `dev.feat-to-surface-map`
- authority_scope: FEAT -> shared design assets ownership mapping
- default_policy: update existing shared asset first
- create_policy: only when a new long-lived boundary is introduced

## Selected FEAT

- feat_ref: `FEAT-AI-COACH-001`
- title: `AI Coach MVP 每日调整与训练后反馈`
- goal: 在不打碎既有主流程骨架的前提下，让用户可以基于每日 readiness 和训练后反馈得到训练计划调整结果。
- scope:
  - 在每日计划查看链路中增加 readiness / adjustment 入口。
  - 在训练完成后增加反馈录入与计划差异回显。
  - 把调整结果限制在既有训练计划与教练主界面内，不扩成新的独立子系统。
- constraints:
  - 不得把 `PROTOTYPE / UI / API / ARCH` 按 FEAT 一对一新建。
  - 必须复用既有 AI 教练主流程骨架与训练计划服务边界。
  - `IMPL` 只能消费已归属的 owner，不得在实施阶段重新发明新的设计口径。
- acceptance_checks:
  - scenario: `daily-adjustment-entry`
    then: 用户可以在每日计划主界面进入调整卡片并看到计划差异。
  - scenario: `post-run-feedback-loop`
    then: 用户提交训练后反馈后，可以看到调整后的下一步计划。
  - scenario: `shared-asset-consistency`
    then: 新增逻辑不要求平行新建 ARCH/API/UI/PROTO 文档。

## Design Impact

- design_impact_required: `true`
- owner_binding_status: `bound`
- bypass_rationale: `N/A`
- create_decision_rule:
  - 本 FEAT 触达多个 shared design assets，但只有 `TECH-PLAN-ADJUSTMENT` 被视为新的长期实现策略包。

## Surface Map

### Architecture

- owner: `ARCH-COACH-MVP-CORE`
- action: `update`
- scope:
  - `daily_adjustment_flow`
  - `post_run_feedback_loop`
- reason: 每日调整与反馈回路仍然属于 AI 教练 MVP 主流程，不应拆成新的架构 owner。

### API

- owner: `API-TRAINING-PLAN`
- action: `update`
- scope:
  - `get_daily_plan`
  - `submit_post_run_feedback`
  - `regenerate_adjusted_plan`
- reason: 这些接口仍归属训练计划服务域，只是增加新的命令/查询 contract。

### UI

- owner: `UI-COACH-CONVERSATION-SHELL`
- action: `update`
- scope:
  - `daily_adjustment_card`
  - `post_run_feedback_entry`
  - `plan_diff_render`
- reason: 新 UI 仍挂在既有 coach shell 内部，不形成新的独立页面骨架。

### Prototype

- owner: `PROTO-MVP-COACH-MAIN`
- action: `update`
- scope:
  - `onboarding_to_daily_plan_transition`
  - `pre_run_adjustment_flow`
  - `feedback_after_run_flow`
- reason: 这些体验流都属于 MVP 主流程骨架，应更新既有 prototype，而不是按 FEAT 切碎。

### TECH

- owner: `TECH-PLAN-ADJUSTMENT`
- action: `create`
- scope:
  - `adjustment decision rules`
  - `readiness evaluation`
  - `feedback-to-plan-regeneration strategy`
- reason: 这里形成了一组后续会被多个 FEAT 复用的长期实现策略包，适合作为新的 TECH owner。

## Ownership Summary

- architecture: `ARCH-COACH-MVP-CORE = update`，因为这是既有 AI 教练主流程扩展。
- api: `API-TRAINING-PLAN = update`，因为仍属于训练计划服务域。
- ui: `UI-COACH-CONVERSATION-SHELL = update`，因为仍属于既有 coach shell。
- prototype: `PROTO-MVP-COACH-MAIN = update`，因为仍属于主 MVP 原型流。
- tech: `TECH-PLAN-ADJUSTMENT = create`，因为需要抽出可复用的长期实现策略包。

## Create Justification

### TECH Create Justification

- owner: `TECH-PLAN-ADJUSTMENT`
- signals:
  - 引入新的长期维护 owner
  - 形成新的状态机 authority
  - 未来会被多个 FEAT 持续复用
- justification: readiness 评估、反馈吸收、计划再生成这组实现策略会被后续“训练前调整”“训练后反馈”“疲劳恢复建议”等 FEAT 共用，继续塞回单个 FEAT 私有 TECH 会导致实现真相源再次碎裂。

## Downstream Handoff

- target_workflows:
  - `workflow.dev.feat_to_tech`
  - `workflow.dev.feat_to_proto`
  - `workflow.dev.proto_to_ui`
  - `workflow.dev.tech_to_impl`
- surface_map_ref: `SURFACE-MAP-FEAT-AI-COACH-001`
- feat_ref: `FEAT-AI-COACH-001`
- gate_expectations:
  - `TECH / PROTO / UI / IMPL` 必须显式回填 `surface_map_ref`
  - `TECH` 必须绑定 `TECH-PLAN-ADJUSTMENT`
  - `PROTO / UI` 必须分别绑定 `PROTO-MVP-COACH-MAIN` 与 `UI-COACH-CONVERSATION-SHELL`
  - `IMPL` 只能消费已解析的 `surface_map_ref / prototype_ref / ui_ref`

## Reverse Traceability

### From FEAT to Shared Assets

- feat_ref: `FEAT-AI-COACH-001`
- related_owner_refs:
  - `ARCH-COACH-MVP-CORE`
  - `API-TRAINING-PLAN`
  - `UI-COACH-CONVERSATION-SHELL`
  - `PROTO-MVP-COACH-MAIN`
  - `TECH-PLAN-ADJUSTMENT`

### Expected Reverse Metadata on Shared Assets

- related_feats:
  - `FEAT-AI-COACH-001`
- last_updated_by:
  - `FEAT-AI-COACH-001`
- open_deltas:
  - `ARCH-COACH-MVP-CORE` 需补充反馈回路状态切换说明
  - `API-TRAINING-PLAN` 需补充 regenerate contract 与错误边界
  - `UI-COACH-CONVERSATION-SHELL` 需补充 plan diff 呈现规则

## Freeze Checklist

- [x] `design_impact_required` 已确认
- [x] 每个受影响设计面都已给出 `owner`
- [x] 每个设计面都已明确 `action=update|create`
- [x] 每个设计面都已明确 `scope`
- [x] 每个设计面都已写出 `reason`
- [x] `TECH-PLAN-ADJUSTMENT` 的 create justification 已补齐
- [x] `Downstream Handoff` 已明确目标 workflow
- [x] 已声明 shared asset 的反向追踪要求
