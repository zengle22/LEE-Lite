---
input_type: adr
title: LL skill-first 主链统一继承源
source_refs:
  - ADR-001
  - ADR-003
  - ADR-006
---

# ADR Merge

## 问题陈述

当前 LL 已分别定义双会话双队列执行架构、文件化 handoff runtime、以及 external gate 的独立 decision/materialization 层，但这三部分仍分散在不同 ADR 中。若下游分别实现，会把同一条主链拆成多个互不对齐的局部机制，因此需要一份 bridge SRC 作为统一继承源。

## 目标用户

- workflow / orchestration 设计者
- governed skill / downstream skill 作者
- gate / reviewer / human loop 设计者
- handoff / audit / artifact 消费方

## 触发场景

- 当主链需要统一 execution loop、gate loop 与 human loop 的协作边界时。
- 当 candidate package 需要交给 gate loop 做最终 decision 与 materialization 时。

## 业务动因

- 需要让双会话双队列、文件化 handoff runtime、external gate 被下游视为同一条治理闭环。
- 需要让 business skill 只产出 candidate package，而 formal object 只在 gate 后物化。
- 需要让审计链稳定回答谁推进了 candidate、谁做了 final decision、为什么允许推进、正式物化了什么对象。

## 关键约束

- 双会话双队列、文件化 handoff runtime、external gate 必须作为同一条治理闭环建模，不能拆成互不约束的三个独立需求。
- business skill 只负责 candidate package、proposal、evidence，不负责最终 gate decision、正式 materialization 或 run closure。
- execution loop、gate loop、human loop 只能通过结构化文件对象协作，不应退回 direct call 或隐式状态共享。
- 下游需求链必须继承这套统一闭环，不得重新发明另一套 queue、handoff、gate、materialization 规则。

## 非目标

- 不展开具体 schema、CLI 或目录实现。
- 不直接做下游需求分解。
