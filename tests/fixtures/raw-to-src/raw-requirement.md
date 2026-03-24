---
input_type: raw_requirement
title: Checkout Retry Messaging
source_refs:
  - interview:2026-03-18-sales-call
  - slack:#payments
constraints:
  - Must not change settlement logic in this phase.
---

# Checkout Retry Messaging

## 问题陈述

用户支付失败后不知道是否应该重试，导致放弃支付和客服咨询同时上升。

## 目标用户

- 首次支付失败的消费者
- 支付客服

## 触发场景

- 银行返回可重试失败码

## 业务动因

- 降低支付流失
- 降低客服重复解释成本

## 非目标

- 不改动支付网关路由
