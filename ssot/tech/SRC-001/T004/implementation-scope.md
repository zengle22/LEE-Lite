# Implementation Scope

## In Scope

- IO Contract schema
- workspace diff collector and evidence join
- structured finding classifier
- consumer mapping to repair / gate / supervision
- bypass unmanaged-consumption evidence detection

## Integration Boundaries

- Gateway 和 Registry 提供 runtime evidence。
- Gateway + Registry guard 是未注册消费的主防线。
- Gate 不重新解释 findings。
- Repair 只消费定位信息。

## Suggested Sequence

1. 冻结 IO Contract 与 severity schema。
2. 实现 auditor 与 finding generation。
3. 最后接 consumer mapping。

## Out Of Scope

- 正式 artifact 写入
- registry read eligibility
- gate decision / materialization
