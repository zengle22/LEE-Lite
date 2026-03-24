# Design Analysis

## Feature Focus

`FEAT-SRC-001-005` 的真正目标是把 decision、materialization、dispatch、run closure 从业务 skill 尾部逻辑中抽离成独立 consumer。它是 formal object 成立的唯一治理边界，但当前还依赖 draft 状态的 `ADR-006` 做专项细化，因此本 TECH 只能先作为 draft 技术包存在。

## Task Signals

- `TASK-FEAT-SRC-001-005-001` 冻结 decision model 与输入契约。
- `TASK-FEAT-SRC-001-005-002` 冻结 materialized object schema 和状态推进。
- `TASK-FEAT-SRC-001-005-003` 冻结 gate-ready consumer 与 evaluator。
- `TASK-FEAT-SRC-001-005-004` 冻结 formal materialization、dispatch 与 run closure。

## Main Technical Tensions

- decision evaluator 和 materializer 容易各自维护状态机。
- audit consumer、registry、gateway 都可能与 gate 交叉吃职责。

## Design Direction

- 以唯一 decision_type 作为后续 materialization plan 的主键。
- formal object 只能由独立 External Gate consumer 物化。
- run closure、spawned refs 和 decision ref 作为同一事务性结果看待。
- gate 可以基于 acceptance/evidence/audit/target constraints 做通过性与去向判定，但不重写业务内容本体。
