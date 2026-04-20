# ADR-051：Task Pack + 顺序执行循环模式

> **SSOT ID**: ADR-051
> **Title**: 采用 Task Pack 结构化任务组 + 顺序执行循环（loop）驱动实施，替代复杂编排
> **Status**: Accepted
> **Version**: v1.0
> **Effective Date**: 2026-04-17
> **Scope**: 执行调度 / 任务管理 / 循环驱动
> **Owner**: 架构 / 执行引擎
> **Governance Kind**: NEW
> **Audience**: AI 实施代理、自动化循环（loop）
> **Depends On**: ADR-018 (Execution Loop Job Runner), ADR-050 (总纲 §7), ADR-047 (双链测试)

---

## 1. 背景

### 1.1 One-Sentence Summary

> **不构建复杂调度系统，采用 Task Pack 结构化任务组 + 顺序执行循环驱动实施，每个 task 完成后触发双链验证，失败即暂停等待人工介入。**

### 1.2 问题

当前执行面存在以下问题：

| 痛点 | 根因 |
|------|------|
| Task 数量多，手动执行效率低 | 缺少结构化任务组织 |
| 编排系统复杂且不稳定 | 过度设计调度层 |
| 执行后不知道测了什么 | task 与双链验证未绑定 |
| 失败 task 被忽略 | 缺少失败暂停机制 |

### 1.3 与 ADR-018 的关系

ADR-018 定义了 Execution Loop Job Runner 的**运行时基础设施**。
本 ADR 定义 **Task Pack 模式** — 即在 ADR-018 运行时之上的任务组织与执行约定。

- ADR-018：提供"怎么跑 loop"的能力
- ADR-051：定义"跑什么、怎么组织、失败了怎么办"

---

## 2. 决策

### 2.1 采用 Task Pack 结构

任务以 Pack 为单位组织，每个 Pack 绑定一个 FEAT：

```yaml
task_pack:
  pack_id: PACK-SRC-001-001-feat001
  feat_ref: FEAT-SRC-001-001
  created_at: 2026-04-17T00:00:00+08:00
  tasks:
    - task_id: TASK-001
      type: impl
      title: Implement API endpoint
      depends_on: []
      status: pending
      verifies: [AC-001, AC-002]

    - task_id: TASK-002
      type: test-api
      title: API test for endpoint
      depends_on: [TASK-001]
      status: pending
      verifies: [AC-001, AC-002]

    - task_id: TASK-003
      type: test-e2e
      title: E2E journey for feature
      depends_on: [TASK-001]
      status: pending
      verifies: [AC-003]

    - task_id: TASK-004
      type: review
      title: Code review
      depends_on: [TASK-002, TASK-003]
      status: pending
      verifies: []
```

### 2.2 Task 类型枚举

| 类型 | 含义 | 触发验证 |
|------|------|---------|
| `impl` | 实现代码 | 无（完成后触发下游 test） |
| `test-api` | API 测试执行 | API 链（ADR-047） |
| `test-e2e` | E2E 测试执行 | E2E 链（ADR-047） |
| `review` | 代码审查 | 审查报告 |
| `doc` | 文档更新 | 无 |
| `gate` | Gate 检查 | Gate 结果 |

### 2.3 顺序执行循环

```
取 Pack 中第一个 depends_on 全满足的 task
  → 执行
  → 更新状态
  → 若 type 为 test-*，触发对应双链验证
  → 若失败 → 暂停 loop，标记 FAILED，等待人工
  → 若成功 → 取下一个可执行 task
  → Pack 所有 task 完成 → Pack 完成
```

### 2.4 执行规则

1. **不做复杂 DAG**：仅支持 `depends_on` 线性/树依赖
2. **不做并发调度**：同时运行的 task 数 ≤ 1
3. **失败即暂停**：任何 task 失败后 loop 停止，不跳过
4. **双链绑定**：test-api 绑定 API 链，test-e2e 绑定 E2E 链
5. **证据回指**：每个 test task 必须在完成后写入 verifies 绑定

### 2.5 Task 状态机

```
pending → running → {passed | failed | skipped}
                          ↓
                    failed → retry (max 2) → still_failed → blocked
```

| 状态 | 含义 |
|------|------|
| `pending` | 等待前置依赖完成 |
| `running` | 执行中 |
| `passed` | 执行成功，验证通过 |
| `failed` | 执行失败，可重试 |
| `still_failed` | 重试后仍失败 |
| `skipped` | 被人工跳过 |
| `blocked` | 因依赖失败无法执行 |

---

## 3. Task Pack 文件位置

```
ssot/tasks/
  PACK-SRC-001-001-feat001.yaml
  PACK-SRC-002-001-feat001.yaml
```

命名规范：`PACK-{SRC_ID}-{FEAT_ID}-{slug}.yaml`

每个 Pack 文件独立，不合并。

---

## 4. Loop 集成

### 4.1 与 ADR-018 Execution Loop Job Runner 的集成

ADR-018 提供 loop 运行时，本 ADR 的 Task Pack 作为 loop 的输入：

```
Execution Loop (ADR-018)
  → 读取 Task Pack YAML
  → 按本 ADR 规则顺序执行
  → 每个 task 后更新状态
  → Pack 完成后触发 Gate（如配置）
```

### 4.2 Loop 配置文件

```yaml
loop:
  mode: sequential
  pack_file: ssot/tasks/PACK-xxx.yaml
  max_retries: 2
  stop_on_failure: true
  verify_after:
    impl: []
    test-api: [api-chain]
    test-e2e: [e2e-chain]
    review: [review-report]
```

---

## 5. 不采纳的方案

### 5.1 复杂 DAG 调度器

不采纳原因：实现复杂、不稳定、当前阶段不需要。顺序 loop 足够。

### 5.2 并发执行

不采纳原因：task 之间存在隐式依赖（如 API 实现 → API 测试 → E2E 测试），并发会导致竞争条件。

### 5.3 失败自动跳过

不采纳原因：跳过失败 task 会积累技术债。暂停等待人工介入是更安全的默认行为。

---

## 6. 后果

### 正面

| 收益 | 说明 |
|------|------|
| 极高稳定性 | 无并发、无竞态、顺序可复现 |
| 实现成本极低 | 基于 ADR-018 loop 运行时，约定即可 |
| 易于调试 | 每个 task 的状态和证据都可追溯 |
| 与双链天然集成 | test task 直接绑定 ADR-047 验证链 |

### 负面

| 代价 | 缓解 |
|------|------|
| 并发能力弱 | 当前阶段不需要，未来可按 Pack 级并行 |
| 大 task 执行时间长 | 拆分 task 粒度（每个 task 聚焦单一 AC） |
| 失败暂停可能阻塞 | 支持人工 skip 快速绕过，后续补测 |

---

## 7. 一句话原则

> **一个 Pack 绑一个 FEAT，一个 loop 顺序跑完，失败即停不跳过，test task 必绑双链。**
