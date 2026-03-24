# Design Analysis

## Feature Focus

`FEAT-SRC-001-003` 的关键不是“再建一个 registry 表”，而是冻结最小 identity contract，并把正式读取资格判断收回 registry-backed reference。

## Task Signals

- `TASK-FEAT-SRC-001-003-001` 已冻结 identity contract 和 registry schema。
- `TASK-FEAT-SRC-001-003-002` 已明确 Gateway 入口与 registry eligibility 的正交边界。

## Main Technical Tensions

- identity contract 若带入 `producer_scope` 等 provenance 字段，会导致 promote / patch 时身份漂移。
- read eligibility 若放回 Gateway 或 Auditor，会重新写散。

## Design Direction

- identity 只保留 `artifact_type + logical_name + stage`，registry record 再承载 provenance。
- formal reference 解析回到 registry。
- read guard fail-closed，未注册对象不得进入正式链路。
