# ADR018 Runner Implementation Plan

日期：2026-03-26

## 目标

把 ADR-018 从“gate 批准后产出 ready job”推进到“runner 自动消费 ready job 并启动下游 workflow”的正式主链，同时消除 review 中发现的三类问题：

- ADR/SRC 状态与代码现实不一致；
- ready-job contract 与现有 writer 漂移；
- CLI/runtime/test surface 在 SSOT 中存在但仓库中缺失。
- gate approve 后缺少显式的 post-approve progression policy，导致不该自动执行的 TESTSET execution job 直接泄漏到 ready queue。

## 分阶段计划

### Phase 0：Contract 对齐

目标：

- 把 ADR-018 从 `Draft` 收敛为已接受决策；
- 把 ready-job schema 与现有代码统一到 `source_run_id`、`formal_ref`、`input_refs`、`authoritative_input_ref`；
- 明确 `ready/claimed/running/done/failed/waiting-human/deadletter` 状态词表。

状态：已完成

输出：

- `ssot/adr/ADR-018-Execution Loop Job Runner 作为自动推进运行时.MD`
- `ssot/src/SRC-003__adr-018-execution-loop-job-runner-作为自动推进运行时.md`
- `cli/lib/ready_job_dispatch.py`

### Phase 1：最小 Runner 主链

目标：

- 增加 `ll loop` 与 `ll job` CLI 入口；
- 实现 ready job claim、run、complete、fail 主链；
- 让 runner 能按 `target_skill` 拉起下游 workflow；
- 为每次执行写入 attempt evidence 和状态快照。

状态：已完成

输出：

- `cli/commands/loop/command.py`
- `cli/commands/job/command.py`
- `cli/lib/job_queue.py`
- `cli/lib/job_state.py`
- `cli/lib/execution_runner.py`
- `cli/lib/skill_invoker.py`
- `cli/lib/job_outcome.py`
- `cli/lib/runner_monitor.py`
- `tests/unit/test_cli_runner_runtime.py`

### Phase 2：主链覆盖扩展

目标：

- 把 runner 覆盖从当前最小链路扩展到更多下游 workflow；
- 补齐 `show-status`、`show-backlog` 在 operator 视角下的稳定输出；
- 明确每类 `target_skill` 的运行入口与 admission 前置条件；
- 把 gate `approve` 后的 `progression_mode` 固化为 `auto-continue | hold`，避免 QA execution 链路被误自动拉起。

状态：已完成

当前已覆盖：

- `workflow.product.src_to_epic`
- `workflow.product.epic_to_feat`
- `workflow.dev.feat_to_tech`
- `workflow.qa.feat_to_testset`
- `workflow.dev.tech_to_impl`
- `formal.testset.* -> skill.qa.test_exec_*` 默认 `hold`

下一步：

- 补一组 end-to-end governed flow 测试，覆盖 gate dispatch 后由 loop 自动推进。
- 强化每条主链的恢复协议和 failure routing。

### Phase 3：恢复与观测补强

目标：

- 把 `retry-reentry`、`waiting-human`、`deadletter` 补成完整恢复协议；
- 增加 claim timeout / lease recovery；
- 强化监控面，输出 backlog、running、failed、deadletter 汇总。

状态：进行中

当前已完成：

- 最小 lease / claim timeout 恢复协议；
- 过期 `claimed/running` job 的 recovery-to-ready；
- `retry-reentry` requeue、`waiting-human`、`deadletter` 基本恢复边界；
- 长任务 lease heartbeat / renew 机制；
- 显式 `ll job renew-lease` 与 `ll loop recover-jobs` 控制面；
- operator 视角的 `show-status` / `show-backlog` 聚合快照；
- `run-execution` 后置监控快照与恢复摘要联动。
- 显式 `ll job release-hold` 控制面；
- 显式 `ll gate release-hold` façade，用于从 gate / dispatch 语义上恢复 hold 下游推进。

下一步：

- 补非法迁移、owner mismatch、retry exhaustion 等更细颗粒度的负向测试；
- 评估是否需要更强的 lease heartbeat/renew 策略，例如续租频率、超时分层与长任务策略；
- 继续补 recovery scan / repair 的 operator 视图细节和恢复操作约束。

## 当前执行顺序

1. 先完成 Contract 对齐，避免 SSOT 和实现继续分叉。
2. 再落最小 Runner 主链，保证 `dispatch -> run-execution -> outcome` 真实可跑。
3. 然后扩展覆盖链路和恢复协议，补上 `progression_mode`、hold 边界和 release 控制面。
4. 最后补全文档、观测与回流能力。

## 验收标准

- gate dispatch 会根据 `progression_mode` 生成 `ready` 或 `waiting-human` job；
- `ll loop run-execution` 能自动消费 ready job 并推进下游 workflow；
- operator 可通过 `ll loop` / `ll job` 完成最小控制与修复；
- operator 可通过 `ll gate release-hold` 或 `ll job release-hold` 恢复被 hold 的下游推进；
- 执行 evidence、状态迁移和 backlog 视图都能被稳定写回；
- SSOT、CLI surface、单元测试三者一致。
