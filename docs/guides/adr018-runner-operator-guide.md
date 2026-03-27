# ADR018 Runner Operator Guide

日期：2026-03-27

## 目标

这份文档面向 runner operator、gate operator 和 QA / workflow owner，说明 ADR-018 当前已经落地的运行方式：

- 哪些下游会自动拉起；
- 哪些下游默认会停在 hold；
- 如何从 skill、loop、gate、job 四个入口操作 runner；
- 如何把 `waiting-human` 的 hold job 释放回 `ready`。

## 核心原则

当前主链遵循两条固定边界：

1. `decision=approve` 只表示“当前对象批准通过”。
2. 是否继续自动拉起下游，由 `progression_mode` 决定：
   - `auto-continue`
   - `hold`

因此，gate 批准后的 dispatch 现在分成两类：

- `auto-continue`：生成 `artifacts/jobs/ready/*.json`，由 runner 自动消费。
- `hold`：生成 `artifacts/jobs/waiting-human/*.json`，等待环境、部署或人工前置满足后再释放。

runner 本身只消费 `ready`，不负责替 gate 猜测“该不该继续”。

## 当前默认策略

截至 2026-03-27，默认策略如下：

- `formal.src.* -> workflow.product.src_to_epic`：默认 `auto-continue`
- `formal.epic.* -> workflow.product.epic_to_feat`：默认 `auto-continue`
- `formal.feat.* -> workflow.dev.feat_to_tech`：默认 `auto-continue`
- `formal.feat.* -> workflow.qa.feat_to_testset`：默认 `auto-continue`
- `formal.tech.* -> workflow.dev.tech_to_impl`：默认 `auto-continue`
- `formal.testset.* -> skill.qa.test_exec_*`：默认 `hold`

`TESTSET -> test_exec` 默认不自动拉起，原因是它依赖环境、部署、账号、权限或 pilot 前置条件。当前系统默认把这类前置条件收敛成：

- `hold_reason = test_environment_pending`
- `required_preconditions = ["test_environment_ref"]`

## 入口分层

### 1. Skill 入口

这是 Claude/Codex 用户的正式入口：

- canonical bundle: `skills/l3/ll-execution-loop-job-runner/`
- installed adapter: `C:\Users\shado\.codex\skills\ll-execution-loop-job-runner`

典型调用：

```powershell
python C:\Users\shado\.codex\skills\ll-execution-loop-job-runner\scripts\runner_operator_entry.py invoke --request req.json --response-out resp.json --evidence-out evidence.json
```

适用场景：

- 从 Codex/Claude 明确启动或恢复 runner
- 不直接关心 repo CLI carrier

### 2. Loop 入口

这是 repo 里的 execution carrier：

```powershell
python -m cli.ll loop run-execution --request req.json --response-out resp.json
python -m cli.ll loop resume-execution --request req.json --response-out resp.json
python -m cli.ll loop show-status --request req.json --response-out resp.json
python -m cli.ll loop show-backlog --request req.json --response-out resp.json
python -m cli.ll loop recover-jobs --request req.json --response-out resp.json
```

适用场景：

- 启动或恢复 ready queue 消费
- 查看 backlog / status / recovery summary
- 修复过期 claimed/running job

### 3. Gate 入口

这是治理视角入口：

```powershell
python -m cli.ll gate dispatch --request req.json --response-out resp.json
python -m cli.ll gate release-hold --request req.json --response-out resp.json
```

适用场景：

- gate 批准后物化 downstream dispatch
- 从 gate/decision 语义上恢复之前被 hold 的推进链路

### 4. Job 入口

这是底层 runtime/operator 入口：

```powershell
python -m cli.ll job claim --request req.json --response-out resp.json
python -m cli.ll job release-hold --request req.json --response-out resp.json
python -m cli.ll job run --request req.json --response-out resp.json
python -m cli.ll job renew-lease --request req.json --response-out resp.json
python -m cli.ll job complete --request req.json --response-out resp.json
python -m cli.ll job fail --request req.json --response-out resp.json
```

适用场景：

- 精确操控单个 job
- 定向恢复、调试、lease renew

## 常见操作

### A. 正常自动推进

适用对象：

- `SRC -> EPIC`
- `EPIC -> FEAT`
- `FEAT -> TECH`
- `FEAT -> TESTSET`
- `TECH -> IMPL`

结果：

- gate dispatch 直接生成 `ready` job
- runner 自动 claim/run/complete/fail

### B. TESTSET 默认 hold

适用对象：

- `TESTSET -> test_exec_cli`
- `TESTSET -> test_exec_web_e2e`

结果：

- gate dispatch 生成 `waiting-human` job
- job 上会带：
  - `progression_mode = hold`
  - `hold_reason = test_environment_pending`
  - `required_preconditions = ["test_environment_ref"]`

### C. 从 gate 视角释放 hold

如果环境已经准备好，推荐使用：

```powershell
python -m cli.ll gate release-hold --request req.json --response-out resp.json
```

最常用 payload：

```json
{
  "dispatch_receipt_ref": "artifacts/active/gates/dispatch/gate-decision-testset-release-dispatch-receipt.json",
  "note": "test environment provisioned"
}
```

也可以直接传：

```json
{
  "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-testset-release.json"
}
```

效果：

- 定位该次 gate dispatch 产生的 `waiting-human` job
- 把它提升到 `artifacts/jobs/ready/`
- 自动把 `progression_mode` 改成 `auto-continue`
- 写入 `hold_released_at` / `hold_released_by`

### D. 从 job 视角释放 hold

如果已经知道具体 job 文件，也可以直接用：

```powershell
python -m cli.ll job release-hold --request req.json --response-out resp.json
```

payload：

```json
{
  "job_ref": "artifacts/jobs/waiting-human/job-release-hold.json",
  "note": "environment is now ready"
}
```

适用场景：

- 调试
- 手动修复
- 不想先定位 gate decision / dispatch receipt

## 关键字段

operator 最常需要看这些字段：

- `decision`
- `progression_mode`
- `dispatch_target`
- `status`
- `queue_path`
- `target_skill`
- `required_preconditions`
- `hold_reason`
- `hold_released_at`
- `hold_released_by`

其中：

- `decision` 决定对象是否批准通过
- `progression_mode` 决定批准后是否继续自动推进
- `status` 决定当前 job 是否会被 runner 消费

## 注意事项

### 1. runner 不消费 `waiting-human`

只有 `ready` 会被 runner 自动消费。`waiting-human` 必须先释放。

### 2. `TESTSET` 默认 hold 是设计要求，不是失败

`TESTSET` 默认进入 `waiting-human` 不是异常，而是为了显式表达执行前置条件尚未满足。

### 3. `gate release-hold` 和 `job release-hold` 不是两套逻辑

两者最终复用同一条底层 release 逻辑。区别只是：

- `gate release-hold` 更贴近治理对象
- `job release-hold` 更贴近运行时对象

### 4. 状态迁移会同步更新 `queue_path`

job 从 `waiting-human -> ready`、`ready -> claimed`、`running -> done/failed` 时，`queue_path` 会与真实落盘目录保持一致。

### 5. `auto-continue` 不替代下游自身校验

如果 gate 显式选择 `auto-continue`，runner 会按决定继续推进；下游 skill 仍然可以根据自己的 contract 再做输入校验。

## 推荐操作顺序

1. 先在 gate 阶段决定是 `auto-continue` 还是 `hold`。
2. 若是 `hold`，先补齐环境/部署/账号等前置条件。
3. 条件满足后，优先用 `gate release-hold` 恢复推进。
4. 如需细粒度修复，再退到 `job release-hold` 或其他 `job/*` 控制面。
