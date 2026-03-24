# Design Analysis

## Feature Focus

`FEAT-SRC-001-004` 的目标不是“做个 diff 工具”，而是建立以 IO Contract 为中心的运行期治理证据链，让 repair、gate 和 supervision 共享同一 finding source。

## Task Signals

- `TASK-FEAT-SRC-001-004-001` 冻结 IO Contract 和 severity model。
- `TASK-FEAT-SRC-001-004-002` 冻结 workspace auditor 和 finding generation。
- `TASK-FEAT-SRC-001-004-003` 冻结 gate / repair / supervision 的 consumer mapping。

## Main Technical Tensions

- 只看文件 diff 容易误判，必须联合 Gateway / Policy / Registry records，并把未注册消费限定为旁路或尝试证据检测。
- consumer 很容易重新解释 findings，导致 audit 语义分裂。

## Design Direction

- 先冻结 contract model，再构建 multi-source auditor。
- finding schema 携带 severity、violation_type、evidence refs 和 minimal_patch_scope。
- consumer 只消费 findings 与 consumer-facing mapping contract，不回写 audit taxonomy。
