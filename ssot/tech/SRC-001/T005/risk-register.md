# Risk Register

## R-001 decision 与 materialization 状态机分裂

- severity: blocker
- mitigation: 以 decision_type 作为唯一 materialization plan 主键，不允许第二套状态机。

## R-002 formal object 重新回流业务 skill

- severity: blocker
- mitigation: formal materialization 只能出现在独立 External Gate consumer 内，不允许上游 skill 直写。

## R-003 ADR-006 前置依赖未冻结

- severity: blocker
- mitigation: 在 `ADR-006` 冻结前，将 TECH-005 保持为 draft，并把 `ADR-005` 标记为上游约束、而不是完整专项规则来源。
