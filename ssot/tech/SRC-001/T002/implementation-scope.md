# Implementation Scope

## In Scope

- rule model schema
- path placement evaluator
- mode decision evaluator
- shared verdict output

## Integration Boundaries

- Gateway 只消费 verdict，不生成 policy。
- Auditor 用相同 verdict 解释违规，不重写规则。

## Suggested Sequence

1. 先落 rule model 和 reason taxonomy。
2. 再实现 path / mode evaluator。
3. 最后接入 Gateway 与 Auditor。

## Out Of Scope

- 正式写入执行
- registry binding
- rollout 迁移计划
