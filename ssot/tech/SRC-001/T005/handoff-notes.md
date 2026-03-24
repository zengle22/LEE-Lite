# Handoff Notes

- contract design 需要先冻结 gate-ready package schema、decision matrix 和 formal object family；在 `ADR-006` 仍为 draft 时，这些对象只应作为预备设计，不应直接进入 active contract baseline。
- DEVPLAN 应把 evaluator、materializer、dispatch、run closure 视为四个连续切片，而不是一个“大 gate 任务”。
- TESTPLAN 重点覆盖五类 decision_type 的互斥性、formal object 输出和 run closure 一致性。
