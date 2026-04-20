# Phase 8: FRZ→SRC 语义抽取链 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 08-frz-src
**Areas discussed:** 抽取策略, 投影不变性守卫, 漂移检测, 级联抽取触发, 锚点注册时机, 测试策略, 范围边界

---

## 抽取策略 (Extract Strategy)

| Option | Description | Selected |
|--------|-------------|----------|
| 规则模板投影 | 基于 FRZ MSC 维度到 SRC 字段的预定义映射规则，确定性输出 | ✓ |
| 语义匹配 + 填充 | 解析 FRZ 语义后用模式匹配填充 SRC 模板 | |

**User's choice:** 规则模板投影
**Notes:** ADR-050 out of scope 明确排除 LLM 语义抽取。与 Phase 7 确定性模式一致。

| Option | Description | Selected |
|--------|-------------|----------|
| 沿用现有 SRC 包格式 | 输出与现有 src_to_epic 相同的 SRC 包结构 | ✓ |
| 新建 FRZ-专用格式 | 定义新的 FRZ-extract 专属输出格式 | |

**User's choice:** 沿用现有 SRC 包格式
**Notes:** FRZ 溯源信息通过 metadata 字段追加。

## 投影不变性守卫 (Projection Guard)

| Option | Description | Selected |
|--------|-------------|----------|
| 抽取后验证 | 抽取完成后比对输出与 FRZ derived_allowed 范围 | ✓ |
| 抽取前预检 + 抽取后验证 | 抽取前检查边界，抽取后再次验证 | |

**User's choice:** 抽取后验证
**Notes:** 与现有 validate_output_package 模式一致。

| Option | Description | Selected |
|--------|-------------|----------|
| 字段白名单 | derived_allowed 是字段名列表 | ✓ |
| MSC 维度锁定 | MSC 5 维为核心不可变，其他均可派生 | |

**User's choice:** 字段白名单
**Notes:** 更精确控制，与 frz_schema.py 已有设计一致。

## 漂移检测 (Drift Detection)

| Option | Description | Selected |
|--------|-------------|----------|
| 锚点级漂移 | 以锚点 ID 为单位检查存在性和语义一致性 | ✓ |
| MSC 维度级漂移 | 检查 5 个 MSC 维度是否完整保留 | |
| 字段级 diff | 逐字段比对 | |

**User's choice:** 锚点级漂移
**Notes:** 复用 anchor_registry.py 基础设施，可追溯无噪声。

| Option | Description | Selected |
|--------|-------------|----------|
| 拦截 + 报告 | 返回 block verdict + 漂移详细报告 | ✓ |
| 拦截 + 自动修正 | 检测到漂移后自动尝试修正 | |

**User's choice:** 拦截 + 报告
**Notes:** 匹配 gate verdict 模式，人类判断更安全。

## 级联抽取触发 (Cascade Trigger)

| Option | Description | Selected |
|--------|-------------|----------|
| 新增 extract 子命令 | 在 src_to_epic.py 和 epic_to_feat.py 中加 extract 子命令 | ✓ |
| frz-manage 统一抽取 | 所有抽取操作集中在 ll frz-manage extract 中完成 | |

**User's choice:** 新增 extract 子命令
**Notes:** 保持技能边界清晰，符合单一职责。

| Option | Description | Selected |
|--------|-------------|----------|
| 手动分步调用 | 每个抽取步骤手动调用 | |
| 一键全链 + 可选分步 | ll frz-manage extract --cascade 一键跑通，保留分步命令 | ✓ |

**User's choice:** 一键全链 + 可选分步
**Notes:** 全链要加上中间的 gate skill，每步抽取后走 gate 审核再继续下一层。范围覆盖整个 SSOT 链（SRC→EPIC→FEAT→TECH/UI/TEST/IMPL），不仅仅是前三层。如果 FRZ 中对应某层的内容信息缺失，需要给出提示。

## 锚点注册时机 (Anchor Registration)

| Option | Description | Selected |
|--------|-------------|----------|
| 抽取时注册 | 抽取时立即注册，实时可追溯 | ✓ |
| Gate 通过后注册 | gate 审核后才注册 | |

**User's choice:** 抽取时注册
**Notes:** 即写即存，立即可追溯。

| Option | Description | Selected |
|--------|-------------|----------|
| 从 FRZ 继承 | FRZ 中的锚点 ID 直接复用到所有下游产物 | ✓ |
| 每层重新生成 | 每层生成新的锚点 ID | |

**User's choice:** 从 FRZ 继承
**Notes:** 端到端追溯，同一 anchor_id 通过不同 projection_path 区分层级。

## 测试策略 (Testing Approach)

| Option | Description | Selected |
|--------|-------------|----------|
| fixture-based 单元测试 | 使用固定 FRZ fixture 验证 | |
| 端到端集成测试 | 跑完整链路验证端到端 | |
| 两者结合 | 单元测试覆盖组件，集成测试覆盖全链路 | ✓ |

**User's choice:** 两者结合
**Notes:** 与 Phase 7 测试规模一致。

| Option | Description | Selected |
|--------|-------------|----------|
| 核心场景全覆盖 | 5 类场景各至少 1 个测试 | ✓ |
| 最小可用集 | 只测试锚点缺失和语义篡改 | |

**User's choice:** 核心场景全覆盖
**Notes:** drift_detector 是核心安全组件，需全覆盖。

## 范围边界 (Scope Boundary)

| Option | Description | Selected |
|--------|-------------|----------|
| 复用现有 gate 逻辑 | 抽取产物走相同 gate 流程，增加锚点检查 | ✓ |
| 新增抽取专用 gate | 为抽取模式新增 gate 类型 | |

**User's choice:** 复用现有 gate 逻辑
**Notes:** 最小变更，不增加 state machine 复杂度。

| Option | Description | Selected |
|--------|-------------|----------|
| 按 ROADMAP 顺序 | drift_detector → frz-manage extract → src-to-epic → epic-to-feat | ✓ |
| 先主入口后支撑 | frz-manage extract 骨架 → drift_detector → 级联 | |
| Claude 自行决定 | 根据依赖关系自行排序 | |

**User's choice:** 按 ROADMAP 顺序
**Notes:** 正确的依赖链顺序。

## Claude's Discretion

- 抽取规则的精确映射表定义
- 全链 --cascade 的具体实现方式
- 缺失内容提示的详细格式和严重级别划分

## Deferred Ideas

- 复杂 DAG 调度器 + 并发执行 — ADR-051 明确不采纳
- 失败自动跳过 — ADR-051 明确失败必须暂停等待人工
- LLM 辅助语义抽取 — ADR-050 out of scope 明确排除
