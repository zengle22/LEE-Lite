# Risk Register

## R-001 identity contract 污染 provenance 字段

- severity: major
- mitigation: path、status、producer provenance、evidence refs 进入 registry record，不进入 identity contract。

## R-002 read eligibility 分散实现

- severity: blocker
- mitigation: 强制所有 managed read 回到 registry-backed guard，其他组件只能消费结果。
