---
id: SRC-007
ssot_type: SRC
title: V2 MVP - 今日训练调整功能简化 (today_session adjustment / micro_adjustment)
status: frozen
version: v1
schema_version: 1.0.0
src_root_id: src-root-src-007
workflow_key: product.raw-to-src
workflow_run_id: frz-smoke-20260408b
source_kind: raw_requirement
source_refs:
- '{''type'': ''file'', ''path'': ''docs/baseline1.0/PRD-001-body-status-input.md'',
  ''description'': ''V1 基线 - 身体状态输入功能 PRD''}'
- '{''type'': ''file'', ''path'': ''docs/baseline1.0/PRD-每日训练调整建议.md'', ''description'':
  ''V1 基线 - 每日训练调整建议 PRD''}'
- '{''type'': ''conversation'', ''date'': ''2026-03-31'', ''description'': ''MVP 简化方案讨论''}'
candidate_package_ref: artifacts/raw-to-src/frz-smoke-20260408b
gate_decision_ref: artifacts/active/gates/decisions/raw-to-src-frz-smoke-20260408b-src-candidate-decision.json
frozen_at: '2026-04-09T05:51:04Z'
---

# V2 MVP - 今日训练调整功能简化 (today_session adjustment / micro_adjustment)

## 问题陈述

当前 V1 基线实现已经将"身体状态输入"和"训练调整"功能做得偏完整，但功能复杂度高、验证目标分散。V2 MVP 需要收敛为最小闭环验证。

## 目标用户

- **主要用户**: 使用佳明/高驰/华为/Apple Watch 的马拉松训练爱好者
- **用户痛点**: 训练计划与实际状态不匹配，容易跑崩或跑伤
- **用户需求**: 根据当天状态快速调整训练，避免受伤

## 触发场景

- 1. **场景 A - 状态良好**: 用户感觉精力充沛，准备按原计划训练
- 输入：fatigue=3
- body=recovered
- brain=clear
- 输出：decision=keep，原计划执行
- 2. **场景 B - 轻度疲劳**: 用户感觉有些疲劳，但未到需要休息的程度
- 输入：fatigue=6
- body=fair
- brain=fair
- 输出：decision=reduce，降低强度
- 3. **场景 C - 明显不适**: 用户感觉身体不适或有疼痛
- 输入：red_flag=true 或 fatigue=8+body=sore
- 输出：decision=rest，建议休息

## 业务动因

- 1. **验证核心价值假设**: 用户需要的是"今日训练修正器"而非"身体状态系统"
- 2. **降低实现风险**: 简化决策模型，避免 LLM+ 规则双轨复杂度
- 3. **加速验证周期**: 单页闭环，减少用户操作步骤

## 冻结输入与需求源快照

- source_snapshot_mode: embedded
- frozen_input_dir: artifacts/raw-to-src/frz-smoke-20260408b/input/
- snapshot_scope: 问题陈述 / 目标用户 / 触发场景 / 业务动因 / 关键约束 / 范围边界
- lineage_refs: {'type': 'file', 'path': 'docs/baseline1.0/PRD-001-body-status-input.md', 'description': 'V1 基线 - 身体状态输入功能 PRD'}, {'type': 'file', 'path': 'docs/baseline1.0/PRD-每日训练调整建议.md', 'description': 'V1 基线 - 每日训练调整建议 PRD'}, {'type': 'conversation', 'date': '2026-03-31', 'description': 'MVP 简化方案讨论'}
- review_rule: 外部 source_refs 仅用于追溯，不是理解候选的前提。

## 内嵌需求源快照

- source_snapshot_mode: embedded
- frozen_input_dir: artifacts/raw-to-src/frz-smoke-20260408b/input/
- snapshot_scope: 问题陈述 / 目标用户 / 触发场景 / 业务动因 / 关键约束 / 范围边界
- frozen_input_ref: artifacts/raw-to-src/frz-smoke-20260408b/input/source-input.md
- frozen_input_sha256: c19e6d9c19dd8b5a3f5abde120d353a4cb657803febe7e44b54ad4c4c76f6ce8
- captured_at: 2026-04-08T08:37:13Z
- original_source_path: E:\ai\LEE-Lite-skill-first\artifacts\raw-input\v2-mvp-today-training-adjust-v4.md
- embedded_title: V2 MVP - 今日训练调整功能简化 (today_session adjustment / micro_adjustment)
- embedded_input_type: raw_requirement
- lineage_refs: {'type': 'file', 'path': 'docs/baseline1.0/PRD-001-body-status-input.md', 'description': 'V1 基线 - 身体状态输入功能 PRD'}, {'type': 'file', 'path': 'docs/baseline1.0/PRD-每日训练调整建议.md', 'description': 'V1 基线 - 每日训练调整建议 PRD'}, {'type': 'conversation', 'date': '2026-03-31', 'description': 'MVP 简化方案讨论'}
- embedded_sections: 问题陈述, 核心闭环 (training-plan closed loop), 目标能力对象 (Target Capability Objects), 产品表面 (Product Surfaces), 运行时对象 (Runtime Objects), 状态机 (States) - DailyAdjustmentFlow, 命令 (Commands), 关键约束, 枚举冻结 (Enum Freezes), 业务动因, 目标用户, 触发场景, 范围边界, 成功标准, API 接口契约, 决策规则 (Decision Rules)
- embedded_body_excerpt: # V2 MVP: 今日训练调整功能简化需求 ## 问题陈述 当前 V1 基线实现已经将"身体状态输入"和"训练调整"功能做得偏完整，但功能复杂度高、验证目标分散。V2 MVP 需要收敛为最小闭环验证。 ## 核心闭环 (training-plan closed loop) **用户补充今天必要状态 → AI 判断今天能不能按原计划练 → 给出调整后的当日计划 → 用户看到更新后的今日训练** 本 MVP 聚焦于 training-plan 模块的 body_checkin + session_feedback → micro_adjustment 日常闭环。 ## 目标能力对象 (Target Capability Objects) ### capability: daily_training_adjustment (today_session adjustment / micro_ad
- review_rule: 外部 source_refs 仅用于追溯，不是理解候选的前提。

## 文档语义层级

- source_layer.role: 高保真冻结需求层
- source_layer.fields: problem_statement, target_users, trigger_scenarios, business_drivers, key_constraints, in_scope, out_of_scope, source_snapshot, frozen_contracts, structured_object_contracts, enum_freezes
- source_layer.consumption_rule: source_layer 是最高优先级事实层；bridge_layer 不得覆盖或重写 source_layer。
- bridge_layer.role: 下游兼容投影层
- bridge_layer.fields: semantic_inventory, target_capability_objects, expected_outcomes, downstream_derivation_requirements, bridge_summary, bridge_context, governance_change_summary
- bridge_layer.consumption_rule: bridge_layer 只负责兼容下游 workflow 的消费视图，不得替代 source_layer 事实定义。
- meta_layer.role: 追溯与治理元数据层
- meta_layer.fields: source_refs, source_provenance_map, normalization_decisions, omission_and_compression_report, contradiction_register, operator_surface_inventory, facet_inference, facet_bundle_recommendation, selected_facets, projector_selection
- meta_layer.consumption_rule: meta_layer 仅用于 lineage、治理和审计，不得重定义业务事实或替代 source_layer。
- precedence_order: source_layer, bridge_layer, meta_layer
- override_rule: 当 source_layer 与 bridge/meta layer 表达不一致时，必须以 source_layer 为准。

## Frozen Contracts

- FC-101: 训练计划 MVP 主链路必须收敛为 min_profile + current_training_state -> risk_gate_result -> plan_draft -> plan_lifecycle(active) -> today_session -> body_checkin + session_feedback -> micro_adjustment，不得回退到完整产品式长链路。
  applies_to=min_profile, current_training_state, risk_gate_result, plan_draft, plan_lifecycle, today_session, body_checkin, session_feedback, micro_adjustment | authoritative_layer=source_layer
- FC-102: risk_gate_result 必须作为生成前内联 gate 运行；不可拆回独立 risk 页面或独立前置流程。
  applies_to=risk_gate_result, plan_draft | authoritative_layer=source_layer
- FC-103: 计划生成必须显式消费 current_training_state，且不得只依据画像、目标或设备占位信息推断训练能力。
  applies_to=current_training_state, risk_gate_result, plan_draft | authoritative_layer=source_layer
- FC-104: 计划草案输出必须以 plan_draft 概览与 today_session 为主，不得把完整解释型全量周表作为 MVP 主交付物。
  applies_to=plan_draft, today_session | authoritative_layer=source_layer
- FC-105: 计划草案不得直接信任 LLM 输出，必须经过规则护栏层校验；违反训练日、长跑日、周跑量增长、高强度连续安排、taper 或伤病约束时必须修正或拒绝。
  applies_to=plan_draft, plan_generation_guardrail, micro_adjustment | authoritative_layer=source_layer
- FC-106: body_checkin 与 session_feedback 必须共同构成日常闭环输入；Daily Adjust 不得只消费训练前状态。
  applies_to=body_checkin, session_feedback, micro_adjustment | authoritative_layer=source_layer
- FC-107: plan_lifecycle 必须显式区分 draft 与 active；同一用户最多一个 active plan，但可存在多个 draft。
  applies_to=plan_lifecycle, plan_draft | authoritative_layer=source_layer
- FC-108: intensity_strategy 在 MVP 阶段必须由系统根据目标、基线、风险和伤病史内部推断，不得作为用户显式风险开关。
  applies_to=risk_gate_result, plan_draft | authoritative_layer=source_layer

## 结构化对象契约

- object: min_profile
  purpose: 以最少输入释放训练计划 draft 生成，不再承载完整画像或设备接入。
  required_fields: age, sex, weight_kg, running_age, current_level_or_best_result, race_type, race_date, goal_priority, weekly_training_days, long_run_day, injury_history_summary, has_current_pain_or_fatigue
  optional_fields: notes
  forbidden_fields: device_binding, history_sync, preferred_time, user_selected_intensity_level, full_report_preferences
  completion_effect: allow_plan_generation=true, risk_gate_input_ready=true
  bridge_split_recommendation: runner_profile_min, plan_goal_min, training_availability_min, risk_hint_min
- object: current_training_state
  purpose: 作为风险 gate 与计划生成的训练能力基线，不依赖设备接入也可手填。
  required_fields: weekly_volume_km, weekly_days, longest_run_km, recent_consistency
  optional_fields: last_race_result, training_continuity, days_since_last_run
  forbidden_fields: device_binding_required, opaque_fitness_score_only
  completion_effect: risk_gate_uses_baseline=true, plan_generator_uses_baseline=true
- object: risk_gate_result
  purpose: 在生成前判断 pass/degraded/blocked，并在 degraded 时重写目标或训练偏好。
  required_fields: outcome, reasons
  optional_fields: downgraded_goal_priority, downgraded_weekly_days, downgraded_quality_sessions, intensity_strategy
  forbidden_fields: standalone_page_state, ui_only_warning
  completion_effect: blocked_stops_generation=true, degraded_rewrites_generation_inputs=true
- object: plan_draft
  purpose: 承载可激活的计划草案，主输出为计划骨架、当前周和 today_session。
  required_fields: plan_status, plan_overview, current_week, today_session, safety_notes
  optional_fields: key_sessions, recovery_weeks, generated_by
  forbidden_fields: standalone_plan_confirm_page, full_explanatory_report_as_primary_output
  completion_effect: allow_activation=true, downstream_primary_output=today_session
- object: today_session
  purpose: 作为用户日常主视图，回答今天练什么、怎么练、什么时候不该练。
  required_fields: session_id, session_type, target_duration_min_or_distance_km, intensity_note, safety_notes, cancel_conditions
  optional_fields: warmup_note, cooldown_note, terrain_note
  forbidden_fields: full_week_table_only, multi_day_report_only
  completion_effect: daily_execution_ready=true
- object: body_checkin
  purpose: 统一生成前与日常训练前身体状态输入，避免两套不一致字段。
  required_fields: fatigue_level, sleep_quality, pain_status, pain_trend, readiness_to_train
  optional_fields: sleep_hours, illness_status, notes
  forbidden_fields: duplicate_precheck_model, page_specific_field_forks
  completion_effect: daily_adjust_input_ready=true
  constraints: pain_trend 必须表达同近期状态相比的新发/加重/持平/改善，而不是仅记录部位。, readiness_to_train=no 时，micro_adjustment 不得继续输出 keep。
- object: session_feedback
  purpose: 记录训练后执行结果，驱动未来 1-3 天或本周余下计划微调。
  required_fields: session_id, completed
  optional_fields: actual_duration_min, actual_distance_km, perceived_exertion, pain_after, deviation_reason, notes
  forbidden_fields: completion_without_session_binding, free_text_only_feedback
  completion_effect: micro_adjustment_can_update_future_sessions=true
  constraints: 当 completed=false 时，必须提供 deviation_reason，不能只留 notes。
  conditional_required_fields: completed=false=deviation_reason
- object: micro_adjustment
  purpose: 基于 body_checkin 与 session_feedback 对未来近端训练做 keep/downgrade/replace/skip。
  required_fields: action, target_scope, rationale
  optional_fields: effective_until, replacement_session
  forbidden_fields: full_plan_regeneration_only, advice_without_action
  completion_effect: near_term_training_updated=true
- object: plan_generation_guardrail
  purpose: 在 risk gate 之后、计划草案输出之前执行运行时规则护栏，避免不安全或不自洽计划进入主输出。
  minimum_checks: weekly_training_days_not_exceeded, long_run_day_within_training_days, weekly_volume_growth_bounded, no_back_to_back_high_intensity, taper_week_reduction_present, injury_risk_session_filter, low_baseline_blocks_aggressive_strategy, race_date_shortfall_forces_degrade
  failure_behavior: rewrite_plan_draft, degrade_goal_or_load, reject_generation
  output_contract: guardrail_passed, guardrail_adjustments, guardrail_failure_reason
- object: plan_lifecycle
  purpose: 冻结训练计划生命周期与 active 唯一性约束。
  required_fields: states, allowed_transitions, active_plan_uniqueness_rule
  optional_fields: terminal_states
  forbidden_fields: page_step_state_machine, multiple_active_plans
  completion_effect: draft_active_boundary_stable=true
  constraints: onboarding 在本 SRC 中指计划实体尚未生成前的 intake runtime state，而非 UI page step。

## 枚举冻结

- field: risk_gate_outcome
  semantic_axis: generation_gate_outcome
  allowed_values: pass, degraded, blocked
  value_definitions: pass=输入通过最小风险门槛，可正常生成计划草案。, degraded=允许生成，但必须先降级目标、训练频次或质量课配置。, blocked=输入不满足最小安全前提，必须阻断生成并返回原因。
  forbidden_semantics: independent_page_state, soft_warning_only, free_text
  used_for: risk_gate_result.outcome, plan_generation_gate, goal_downgrade, training_load_rewrite
- field: goal_priority
  semantic_axis: goal_outcome_priority
  allowed_values: finish, pb
  value_definitions: finish=优先安全完赛与稳定执行。, pb=在安全边界内争取成绩提升。
  forbidden_semantics: motivation_copy, training_style, free_text
  used_for: risk_gate_result, plan_draft, micro_adjustment
- field: recent_consistency
  semantic_axis: recent_training_continuity
  allowed_values: none, low, medium, high
  value_definitions: none=最近基本未形成连续训练。, low=有零散训练，但连续性较弱。, medium=已有较稳定训练习惯，但仍需保守推进。, high=近阶段训练连续性稳定，可承接更系统训练安排。
  forbidden_semantics: fitness_score, race_level, free_text
  used_for: current_training_state, risk_gate_result, plan_draft
- field: micro_adjustment_action
  semantic_axis: near_term_plan_adjustment
  allowed_values: keep, downgrade, replace, skip
  value_definitions: keep=维持原训练安排。, downgrade=保留训练目的但降低强度、时长或距离。, replace=替换为更安全的训练内容。, skip=本次训练取消，恢复优先。
  forbidden_semantics: long_term_plan_regeneration, coach_note_only, free_text
  used_for: today_session, micro_adjustment, session_feedback
- field: micro_adjustment_target_scope
  semantic_axis: near_term_adjustment_window
  allowed_values: next_session, next_3_days, rest_of_week
  value_definitions: next_session=只调整下一次训练。, next_3_days=调整未来三天内的训练安排。, rest_of_week=调整本周余下训练安排。
  forbidden_semantics: full_plan_scope, free_text, user_interface_label
  used_for: micro_adjustment, today_session
- field: readiness_to_train
  semantic_axis: same_day_execution_readiness
  allowed_values: yes, uncertain, no
  value_definitions: yes=当前状态允许按计划执行。, uncertain=当前状态存在不确定性，需要保守处理或降级。, no=当前状态不适合执行原计划，应跳过或替换。
  forbidden_semantics: motivation_only, free_text, page_copy
  used_for: body_checkin, micro_adjustment, today_session
- field: pain_trend
  semantic_axis: same_day_pain_direction
  allowed_values: new, worse, same, better
  value_definitions: new=出现新的疼痛或不适。, worse=既有疼痛明显加重。, same=疼痛状态与近期基线相近。, better=疼痛较近期基线改善。
  forbidden_semantics: body_part_only, free_text, severity_score_only
  used_for: body_checkin, risk_gate_result, micro_adjustment
- field: plan_lifecycle_status
  semantic_axis: plan_runtime_status
  allowed_values: onboarding, draft, active, completed, cancelled
  value_definitions: onboarding=计划实体尚未生成前的 intake runtime state，而非 UI page step。, draft=计划草案已生成，但尚未激活。, active=当前唯一有效训练计划。, completed=计划按生命周期完成。, cancelled=计划已停止，不再继续执行。
  forbidden_semantics: page_step, ui_tab, free_text
  used_for: plan_lifecycle, plan_draft, today_session
- field: deviation_reason
  semantic_axis: why_session_deviated
  allowed_values: schedule_conflict, fatigue, pain, illness, motivation_low, environmental, unknown
  value_definitions: schedule_conflict=因时间或日程冲突未按计划完成。, fatigue=因疲劳过高未按计划完成。, pain=因疼痛或伤病风险未按计划完成。, illness=因生病或身体异常未按计划完成。, motivation_low=因动力不足未按计划完成。, environmental=因天气、场地等外部环境未按计划完成。, unknown=用户未给出明确原因。
  forbidden_semantics: long_form_note_only, free_text_only
  used_for: session_feedback, micro_adjustment
- field: intensity_strategy
  semantic_axis: system_derived_training_aggressiveness
  allowed_values: conservative, standard, stretched
  value_definitions: conservative=安全优先，适合较高风险或较低基线。, standard=默认平衡策略。, stretched=在安全前提下略有进取，但仍受规则护栏层约束。
  forbidden_semantics: user_direct_choice, aggressive_label, free_text
  used_for: risk_gate_result, plan_draft

## 语义清单

- Actors: **主要用户**: 使用佳明/高驰/华为/Apple Watch 的马拉松训练爱好者; **用户痛点**: 训练计划与实际状态不匹配，容易跑崩或跑伤; **用户需求**: 根据当天状态快速调整训练，避免受伤
- Core objects: min_profile; current_training_state; risk_gate_result; plan_draft; today_session; body_checkin; session_feedback; micro_adjustment; plan_generation_guardrail; plan_lifecycle
- Core states: onboarding; draft; active; completed; cancelled
- Current API anchors: POST /v1/plans/smart-generate; POST /v1/plans/{plan_id}/activate; POST /v1/plans/check-in; POST /v1/plans/session-feedback; POST /v1/ai/coach/daily-adjust
- Core outputs: plan_overview; current_week; today_session; safety_notes; micro_adjustment
- Product surfaces: minimal_plan_intake; plan_draft_review; today_session_card; daily_checkin; session_feedback_sheet
- Operator surfaces: None
- Entry points: minimal_plan_intake; plan_draft_review; today_session_card
- Commands: None
- Runtime objects: current_training_state; risk_gate_result; plan_draft; today_session; body_checkin; session_feedback; micro_adjustment; plan_generation_guardrail; plan_lifecycle
- States: onboarding; draft; active; completed; cancelled
- Observability surfaces: None

## 标准化决策

- source_projection: 将原始输入统一映射为主链兼容的标准字段。 (loss_risk=low)
- bridge_projection: 为下游 workflow 提供兼容的 bridge projection，同时保留 high-fidelity source layer。 (loss_risk=medium)
- semantic_layer_separation: 显式声明 source / bridge / meta 的优先级，避免下游把桥接层误当成原始事实层。 (loss_risk=low)
- machine_contract_extraction: 把分散在 prose 中的关键冻结事实收敛成机器优先的契约结构，降低下游继承漂移。 (loss_risk=low)

## 压缩与省略说明

- Compressed: problem_statement | why=正文会被整理为适合下游消费的规范化问题陈述。 | risk=low
- Compressed: bridge_context | why=bridge projection 会把 raw 中分散的治理语义压缩为统一继承视图。 | risk=medium
- Summary: SRC 同时保留 high-fidelity source layer 和 bridge projection；任何压缩都必须显式记录。

## Operator Surface Inventory

- 未检测到需要冻结为独立 CLI/skill 的 operator surface，但已识别业务入口与 API command surface。

## 用户入口与控制面

- 未检测到需要冻结为独立 skill / CLI control surface 的显式用户入口；业务入口与 command surface 已在语义清单中冻结。

## 冲突与未决点

- No explicit contradictions detected during normalization.

## 目标能力对象

- min_profile
- current_training_state
- risk_gate_result
- plan_draft
- today_session
- body_checkin
- session_feedback
- micro_adjustment
- plan_generation_guardrail
- plan_lifecycle

## 成功结果

- 用户用最少输入即可获得可执行的训练计划草案，并能在激活后直接看到 today_session。
- 风险评估不再独立成页，而是在生成前以内联 gate 形式稳定执行。
- 系统可根据 body_checkin 与 session_feedback 对未来 1-3 天或本周余下训练给出微调。

## 治理变更摘要

- MVP 生成输入补齐 current_training_state，不再只依赖画像与目标做弱推断。
- Daily Adjust 从附属功能提升为闭环核心，必须同时消费 body_checkin 与 session_feedback。
- 计划生命周期从页面步骤导向切换为 onboarding / draft / active / completed / cancelled。
- 计划生成 guardrail 从隐式逻辑提升为显式运行时对象，避免下游把它漂移成 prompt 约定。

## 下游派生要求

- 下游 EPIC / FEAT / TASK 必须继承 current_training_state 作为生成与风控的能力基线输入。
- 若下游需要展开 intake/API 设计，应优先将 min_profile 投影为 runner_profile_min、plan_goal_min、training_availability_min、risk_hint_min 四个 bridge-level 子对象。
- today_session 必须继续作为日常主输出，完整周表只能作为附属视图。
- session_feedback 与 micro_adjustment 不得在后续层被降级为可选增强项。
- plan_lifecycle 必须保持 draft / active 分离且只允许一个 active。
- plan_generation_guardrail 必须作为运行时对象显式存在，不能只埋在 prompt 或测试用例里。

## 关键约束

- ### constraint: minimal_input_contract
- **描述**: MVP 阶段只保留 3 必填 +1 可选 +1 红旗字段
- **规则**:
- fatigue_level: 必填，0-10
- body_state: 必填，三选一
- brain_state: 必填，三选一
- sleep_hours: 可选
- red_flag: 必填，布尔值
- ### constraint: three_value_decision
- **描述**: 决策只输出 keep/reduce/rest 三档
- **规则**:
- 不允许 upgrade 升档
- 不允许复杂评分 breakdown
- 不允许 LLM 生成建议 (纯规则引擎)
- ### constraint: single_page_flow
- **描述**: 整个流程在单页面完成
- **规则**:
- 不跳转到独立建议页
- 不跳转到独立确认页
- 在当前页完成输入→建议→应用

## 范围边界

- In scope: 围绕《V2 MVP - 今日训练调整功能简化 (today_session adjustment / micro_adjustment)》建立稳定、可追溯的需求源。
- Out of scope: 下游 EPIC/FEAT/TASK 分解与实现细节。

## 来源追溯

- Source refs: {'type': 'file', 'path': 'docs/baseline1.0/PRD-001-body-status-input.md', 'description': 'V1 基线 - 身体状态输入功能 PRD'}, {'type': 'file', 'path': 'docs/baseline1.0/PRD-每日训练调整建议.md', 'description': 'V1 基线 - 每日训练调整建议 PRD'}, {'type': 'conversation', 'date': '2026-03-31', 'description': 'MVP 简化方案讨论'}
- Input type: raw_requirement
- SSOT policy: src candidate must remain reviewable even if the original external requirement file is later removed.

## 桥接摘要

- 训练计划模块从完整产品式长链路收缩为生成、执行、反馈、微调的最小闭环。
- 风险评估与计划生成被收敛为同一条生成链：校验输入 -> risk gate -> 生成草案 -> 规则护栏层 -> 输出。
- 计划主输出从完整解释型周表改为 plan_draft 概览与 today_session。

## Bridge Context

- 结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。
- governed_by_adrs: {'type': 'file', 'path': 'docs/baseline1.0/PRD-001-body-status-input.md', 'description': 'V1 基线 - 身体状态输入功能 PRD'}, {'type': 'file', 'path': 'docs/baseline1.0/PRD-每日训练调整建议.md', 'description': 'V1 基线 - 每日训练调整建议 PRD'}, {'type': 'conversation', 'date': '2026-03-31', 'description': 'MVP 简化方案讨论'}
- change_scope: 训练计划模块 2.0 MVP 只冻结生成 -> 执行 -> 反馈 -> 微调最小闭环，不继续扩成完整产品链路。
- governance_objects: min_profile; current_training_state; risk_gate_result; plan_draft; today_session; body_checkin; session_feedback; micro_adjustment; plan_generation_guardrail; plan_lifecycle
- current_failure_modes: 主链路过长，用户在看到今日训练卡前需要完成过多输入、页面与可选集成。; 风险评估与计划生成分离，导致前端状态分叉和后端降级逻辑不稳定。; 缺少 current_training_state，目标可行性和训练负荷判断不扎实。; Daily Adjust 只消费训练前状态，无法根据执行结果形成真正收敛。; guardrail 没有对象化时，容易在实现层被拆成隐式逻辑、prompt 约定或测试规则，导致运行时分叉。
- downstream_inheritance_requirements: 下游 EPIC / FEAT / TASK 必须继承 current_training_state 作为生成与风控的能力基线输入。; 若下游需要展开 intake/API 设计，应优先将 min_profile 投影为 runner_profile_min、plan_goal_min、training_availability_min、risk_hint_min 四个 bridge-level 子对象。; today_session 必须继续作为日常主输出，完整周表只能作为附属视图。; session_feedback 与 micro_adjustment 不得在后续层被降级为可选增强项。; plan_lifecycle 必须保持 draft / active 分离且只允许一个 active。; plan_generation_guardrail 必须作为运行时对象显式存在，不能只埋在 prompt 或测试用例里。
- expected_downstream_objects: runner_profile_min, plan_goal_min, training_availability_min, risk_hint_min, plan_generation_guardrail
- acceptance_impact: 用户用最少输入即可获得可执行的训练计划草案，并能在激活后直接看到 today_session。; 风险评估不再独立成页，而是在生成前以内联 gate 形式稳定执行。; 系统可根据 body_checkin 与 session_feedback 对未来 1-3 天或本周余下训练给出微调。
- non_goals: 下游 EPIC/FEAT/TASK 分解与实现细节。
- recommended_min_profile_split: runner_profile_min; plan_goal_min; training_availability_min; risk_hint_min
- current_api_anchors: current_api_anchor: POST /v1/plans/smart-generate; current_api_anchor: POST /v1/plans/{plan_id}/activate; current_api_anchor: POST /v1/plans/check-in; current_api_anchor: POST /v1/plans/session-feedback; current_api_anchor: POST /v1/ai/coach/daily-adjust
