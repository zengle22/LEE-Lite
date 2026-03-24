# Handoff Notes

- 下游 contract design 需要先冻结 verdict schema 和 reason code，再对接 Gateway / Auditor。
- DEVPLAN 应把 rule model 与 evaluator 实现拆成两个连续切片，不建议混成单任务。
- TESTPLAN 重点覆盖非法 root、命名漂移和 mode 冲突矩阵。
