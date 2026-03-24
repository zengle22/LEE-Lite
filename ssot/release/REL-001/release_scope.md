# REL-001 Release Scope

## Scope Summary

`REL-001` 组织的是一组围绕 Managed Artifact IO 治理底座的 FEAT Bundle，而不是一个单点功能发版。这个 RELEASE draft 的目的是把 `SRC-001` 已经冻结的治理链上游对象，收束成后续 DEVPLAN 和 TESTPLAN 都能消费的正式范围对象。该对象冻结的是规划基线，不是执行结果。

## Included FEATs

- `FEAT-SRC-001-001`: Managed Artifact Gateway 受管操作入口
- `FEAT-SRC-001-002`: Path Policy 与写入模式判定
- `FEAT-SRC-001-003`: Artifact Identity 与 Registry 正式登记
- `FEAT-SRC-001-004`: Runtime Audit 与 IO Contract 执行
- `FEAT-SRC-001-005`: External Gate Decision 与正式物化

## Included TASK Bundle

- Task root: `ssot/tasks/SRC-001`
- Included task manifest: `ssot/release/REL-001/included_tasks.json`
- Total TASK count: 13
- Highest-density work area: `FEAT-SRC-001-005`
- Scope rule: 只有 `included_tasks.json` 中列出的 TASK 视为本 RELEASE 范围内对象，不能把整个 `ssot/tasks/SRC-001` 根目录默认为全量纳入。

## Release Intent

- 为下游 `release-to-devplan` 提供稳定的 FEAT / TASK 聚合范围。
- 为下游 `release-to-testplan` 提供 acceptance、risk、audit、gate 相关测试种子。
- 保持 RELEASE 仍为 `draft`，不提前替代 downstream freeze。
- 将 `release_window` 定义为 planning window，而不是最终上线窗口。

## Freeze Boundary

- 冻结对象：`feat_refs`、`derived_from_ids` 指定的 FEAT 版本、`included_tasks.json` 中列出的 TASK 基线、`feat_dependency_matrix.json` 中的规划依赖关系。
- 非冻结对象：DEVPLAN、TESTPLAN、执行 evidence、进度状态、最终发布裁决。
- 变更规则：若 scope、version、task selection 或 dependency matrix 发生实质变化，应新建 REL revision。

## Out Of Scope

- DEVPLAN 任务排期细化
- TESTPLAN 策略与用例细化
- Go/No-Go 最终发布裁决
- 运行态 evidence 汇总或闭环结果统计
