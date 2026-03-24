# Implementation Scope

## In Scope

- gate-ready package normalization and validation
- unique decision evaluator
- formal materialization plan
- dispatch routing and run closure writing

## Integration Boundaries

- Gateway 提供正式写入 surface。
- Registry 提供 formal reference 与资格约束。
- Audit 提供 gate-facing findings，不重新参与 decision。
- `ADR-005` 提供已冻结治理前置；`ADR-006` 当前仅提供 draft 专项细化。

## Suggested Sequence

1. 先冻结 decision model 和 object schemas。
2. 再实现 consumer / evaluator。
3. 最后接 materializer、dispatch 和 run closure。

## Out Of Scope

- 业务语义重审
- 人类审批责任替代
- 重型 runtime 基础设施要求
