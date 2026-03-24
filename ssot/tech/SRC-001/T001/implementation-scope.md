# Implementation Scope

## In Scope

- 定义 Gateway runtime entrypoints 与统一 dispatcher。
- 接入 Path Policy verdict 与 Registry binding prerequisites。
- 输出 success / deny / failure / staging evidence 回执。

## Integration Boundaries

- Path Policy 只提供 verdict，不执行正式写入。
- Registry 只提供 binding / eligibility hook，不接管 Gateway surface。
- Audit 只消费 receipt 和 evidence，不回写执行结果。

## Suggested Sequence

1. 先冻结 request / receipt contract。
2. 再实现 runtime dispatcher 与 handler。
3. 最后接入 fail-closed path 和 observability。

## Out Of Scope

- Path Policy 规则细节
- Registry identity model
- Audit finding 生成
