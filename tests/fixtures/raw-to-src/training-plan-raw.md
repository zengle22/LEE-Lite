---
input_type: raw_requirement
title: Smart Plan Generation V2 MVP
source_refs:
  - interview:2026-03-25-training-coach
  - doc:training-plan-spec-v1
constraints:
  - Must support daily adjustment
  - Must track session feedback
---

# Smart Plan Generation V2 MVP

## 问题陈述

当前训练计划缺乏闭环反馈机制，用户执行后无法微调，导致计划与实际能力脱节。

## 目标用户

- 使用训练计划的跑步爱好者
- 跑步教练

## 触发场景

- 用户完成每日训练后提交反馈
- 系统根据反馈微调次日计划

## 业务动因

- 提升训练计划完成率
- 降低运动损伤风险

## 关键状态

- current_training_state: 当前训练状态
- risk_gate_result: 风险门评估结果
- plan_draft: 计划草稿
- today_session: 今日训练卡
- body_checkin: 身体打卡
- session_feedback: 训练反馈
- micro_adjustment: 微调决策
- plan_lifecycle: 计划生命周期

## 对象模型

- min_profile: 最小用户档案
- weekly_volume_km: 周跑量
- longest_run_km: 最长距离
- recent_consistency: 近期一致性
- taper: 减量期标记

## 工作流

1. 用户完成训练 -> 提交 session_feedback
2. 系统评估 risk_gate_result
3. 生成 micro_adjustment
4. 更新 today_session
5. 进入下一训练周期

## 枚举值

- training_state: draft, active, paused, completed
- risk_level: low, medium, high
- adjustment_type: increase, maintain, decrease, rest
