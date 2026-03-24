# Implementation Scope

## In Scope

- minimal identity contract
- registry record schema and status transition
- registry binding hooks
- managed read eligibility guard
- provenance fields separated from identity key

## Integration Boundaries

- Gateway 负责 read surface，不负责 eligibility。
- Gateway 的所有 managed read 都必须委托 registry-backed guard。
- Auditor 与 External Gate 只消费 read eligibility 结果。

## Suggested Sequence

1. 先冻结 identity contract 与 registry schema。
2. 再接入 binding hooks。
3. 最后接入 formal reference 解析和 read guard。

## Out Of Scope

- path policy decisions
- workspace audit
- handoff / materialization graph
