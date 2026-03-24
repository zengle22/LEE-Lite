# Design Analysis

## Feature Focus

`FEAT-SRC-001-001` 的核心不是“提供一个文件工具类”，而是建立正式 artifact 的唯一操作面。它的治理价值在于把 write / commit / promote / append_run_log 从 skill 内部路径写入，提升为受管执行链路。

## Task Signals

- `TASK-FEAT-SRC-001-001-001` 已冻结 Gateway contract 和 receipt 模型。
- `TASK-FEAT-SRC-001-001-002` 明确要求 runtime 入口、policy/registry 接入和 fail-closed 保护。

## Main Technical Tensions

- Gateway 既要统一操作面，又不能吞掉 Path Policy 和 Registry 职责。
- 成功 / 拒绝 / 失败三类回执都必须足够稳定，才能被 Audit 和 External Gate 消费。
- 兼容期最容易出现“失败后偷偷直写”的旁路。

## Design Direction

- 以 dispatcher + preflight + receipt factory 组织 Gateway。
- 所有正式写路径先过 policy / registry prerequisites，再进入 handler。
- 失败路径只允许 staging retention 和 error evidence。
