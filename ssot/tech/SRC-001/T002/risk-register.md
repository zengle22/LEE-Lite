# Risk Register

## R-001 Policy bundle 版本漂移

- severity: major
- mitigation: Gateway 与 Auditor 均引用同一 policy bundle version。

## R-002 Reason code 失控膨胀

- severity: major
- mitigation: 在 contract design 前冻结最小 taxonomy，禁止临时追加自由文本错误码。
