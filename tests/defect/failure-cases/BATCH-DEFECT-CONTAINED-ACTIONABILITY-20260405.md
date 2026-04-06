# formerly contained cases actionability（2026-04-05）

## 结论

这 2 个 case 在关闭前都处于 `contained` 状态，且不能在当前工作树里直接继续做“内容侧修复”，因为它们的 `repair_context.allowed_edit_scope` 指向的主要目标已经不存在。

这不是 guard 没补完，而是 **case 指向的修复对象与当前 workspace 已经漂移**。

## FC-20260402-171755-SRC001-P

- 当前状态：`blocked_missing_targets`
- 缺失目标：
  - `ssot/impl/SRC-001`
  - `ssot/testset/SRC-001`
  - `ssot/ui/SRC-001`
- 当前仍存在：
  - `ssot/tech/SRC-001`
- 影响：
  - 不能在当前 workspace 直接补 recovery/state-closure/TESTSET/UI authority 内容。
- 建议下一步：
  - 恢复原始 SRC001 suite 对应对象，或
  - 基于当前主线对象重新 capture 一次 failure package。

## FC-20260403-053640-SRC002-F

- 当前状态：`blocked_missing_targets`
- 缺失目标：
  - `ssot/impl/SRC-002`
  - `ssot/ui/SRC-002`
  - `ssot/api/SRC-002`
- 当前仍存在：
  - `ssot/testset`
- 影响：
  - 不能在当前 workspace 直接补 IMPL/UI/API authority 与 implementation unit mapping 内容。
- 建议下一步：
  - 恢复原始 SRC002 suite 对应对象，或
  - 基于当前主线对象重新 capture 一次 failure package。

## 判断

- 批次层面已经没有 `open` case。
- 这两条已按用户决策关闭，但关闭前的可操作性判断仍保留在此，供后续追溯。
- 在当前 workspace 继续硬修这两条，会变成“修现在的主线对象”，而不是“修 case 指向的原对象”。
