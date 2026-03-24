# Design Analysis

## Feature Focus

`FEAT-SRC-001-002` 的核心是把路径与 mode 的治理从 skill 经验规则提升为统一政策源。它不是简单的路径白名单，而是正式链路的准入判定层。

## Task Signals

- `TASK-FEAT-SRC-001-002-001` 已冻结 rule model。
- `TASK-FEAT-SRC-001-002-002` 已明确 evaluator 实现和 Gateway / Auditor 共用要求。

## Main Technical Tensions

- 路径、命名和 mode 属于不同维度，混写会降低可解释性。
- 若 Gateway 与 Auditor 读到不同版本的 policy，治理结论会失真。

## Design Direction

- 用分层 rule bundle 管理 root / placement / naming / mode。
- 统一输出 machine-readable verdict 和 reason code。
- 将 evaluator 视为共享依赖，不在消费方复制判断逻辑。
