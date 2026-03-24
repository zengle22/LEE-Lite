# Risk Register

## R-001 审计误报过多

- severity: major
- mitigation: contract、policy verdict、registry record 联合求值，不直接以 diff 下结论。

## R-002 consumer 语义漂移

- severity: major
- mitigation: gate / repair / supervision 只消费 findings，不定义新的 severity 体系。
