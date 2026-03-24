---
artifact_type: src_candidate
workflow_key: product.raw-to-src
workflow_run_id: raw-to-src-20260320T101500Z
title: Checkout Retry Messaging
status: freeze_ready
source_kind: raw_requirement
source_refs:
  - interview:2026-03-18-sales-call
  - slack:#payments
---

# Checkout Retry Messaging

## 问题陈述

支付失败后的重试指引不明确，导致用户流失和客服压力上升。

## 目标用户

- 首次支付失败的消费者
- 支付客服

## 触发场景

- 银行返回可重试失败码

## 业务动因

- 降低支付流失
- 降低客服重复解释成本

## 关键约束

- 不改动支付网关路由

## 范围边界

- In scope: 失败后的消息文案与引导策略
- Out of scope: 网关策略和清结算逻辑

## 来源追溯

- Source refs: interview:2026-03-18-sales-call, slack:#payments
- Input type: raw_requirement
