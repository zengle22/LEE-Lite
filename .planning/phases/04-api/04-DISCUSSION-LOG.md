# Phase 4: API 链全流程试点 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-14
**Phase:** 04-api
**Areas discussed:** 试点 feat 选择, 执行方式, 证据生成, 失败处理

---

## 试点 feat 选择

| Option | Description | Selected |
|--------|-------------|----------|
| 使用现有 api-test-plan | 已有的 FEAT-SRC-001-001 到 005-001 中任选一个 | |
| 新建最小 feat | 新建一个干净的 feat YAML，确保输入格式完全符合 Phase 1 的 schema | ✓ |
| 从 src-to-epic 产出 | 用 Phase 2 的 feat-to-apiplan 技能自动生成 api-test-plan | |

**User's choice:** 新建最小 feat
**Notes:** 新建的 feat 应包含 2-3 个 API 对象、3-5 个 capabilities、覆盖 P0/P1 优先级

## 执行方式

| Option | Description | Selected |
|--------|-------------|----------|
| 单步交互式 | 一个 skill 调完后停下来检查结果，确认通过再调下一个。首次试点最安全。 | ✓ |
| 脚本批量 | 写一个 shell 脚本把所有 skill 串起来自动跑，中间不暂停 | |
| 手工逐个调用 | 每个 skill 单独手动调用 ll skill 命令 | |

**User's choice:** 单步交互式（推荐）
**Notes:** 首次试点需要观察每个环节的输出，不追求全自动批量

## 证据生成

| Option | Description | Selected |
|--------|-------------|----------|
| 执行后自动标记 | 测试执行后自动在 manifest 对应 item 上标记 lifecycle_status 和 evidence_status | ✓ |
| 手工更新 manifest | 测试执行完毕后手工更新 manifest 的状态字段 | |
| 独立 evidence 文件 | 单独写一个 evidence YAML 文件记录执行结果 | |

**User's choice:** 执行后自动标记（推荐）
**Notes:** evidence 作为独立文件存放在 `ssot/tests/.artifacts/evidence/` 目录下，按 coverage_id 命名

## 失败处理

| Option | Description | Selected |
|--------|-------------|----------|
| 停止并记录 | 链中任意环节失败时停止执行，记录失败原因到 pilot-report，不回退已完成的部分 | ✓ |
| 重试上一步 | 失败后尝试回退到上一步重新生成，最多重试 2 次 | |
| 跳过继续 | 如果某步失败了，跳过它继续往下跑 | |

**User's choice:** 停止并记录（推荐）
**Notes:** 已完成的中间产物保留，便于调试和排查

---

## Claude's Discretion

- 最小 feat YAML 的具体内容（API 对象、capabilities 选择）
- 测试执行时的具体断言验证方式
- pilot-report 的详细格式

## Deferred Ideas

- E2E 链全流程试点（v2 REQ-10）— 后续阶段
- Python 生产级 CLI 运行时（v2 REQ-20）— 后续阶段
- CI 接入 release gate（v2 REQ-21）— 后续阶段
