# Risk Register

## R-001 Gateway 侵占依赖职责

- severity: major
- mitigation: 只允许 Gateway 做编排和 receipt，不承载 policy / identity 规则本体。

## R-002 兼容期直写旁路残留

- severity: blocker
- mitigation: feature flag 下也保持写路径 fail-closed，不允许 direct write fallback。
