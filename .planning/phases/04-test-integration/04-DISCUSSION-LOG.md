# Phase 4: 测试联动规则 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 04-test-integration
**Areas discussed:** Manifest marking strategy, Harness adaptation, test_impact enforcement, Conflict resolution, File architecture

---

## 5 角色评审结果

| 角色 | CRITICAL | HIGH | MEDIUM | LOW |
|------|----------|------|--------|-----|
| Factual | 2 | 2 | 2 | 1 |
| Security | 1 | 2 | 2 | 1 |
| Senior Eng | 2 | 2 | 3 | 2 |
| Consistency | 0 | 4 | 5 | 1 |
| Redundancy | 0 | 0 | 2 | 3 |

---

## 用户决策

### test_impact 表示法

| Option | Description | Selected |
|--------|-------------|----------|
| Boolean flags（不改 schema） | 保持 ADR-049 已有的 boolean flags 设计，REQUIREMENTS.md 的枚举定义是过时/错误的 | ✓ |
| Enum（改 schema 对齐 REQ） | 改为枚举类型，代码更简洁，每个 Patch 只声明一种影响类型 | |
| 两者都保留 | enum + flags，语义最完整但实现最重 | |

**Notes:** 用户选择最小改动方案，保持现有 boolean flags 设计不变。

### Manifest 标记策略

| Option | Description | Selected |
|--------|-------------|----------|
| 新字段 + 不改状态机 | 在 manifest schema 中新增 `patch_affected: boolean` + `patch_refs: [string]`，不动 lifecycle_status | ✓ |
| 扩展 lifecycle_status 枚举 | 新增 `needs_regeneration` 值，并定义回退转换规则 | |

**Notes:** 用户选择不违反 ADR-047 状态机的方案，新增独立字段标记受 Patch 影响的 item。

---

## Claude's Discretion

- `patch_affected` 和 `patch_refs` 字段的具体 schema 定义格式
- resolve_patch_context() 的具体 struct 设计
- 冲突检测统一后旧函数的迁移策略（保留兼容 vs 直接替换）
- reviewed_at 的具体格式

## Deferred Ideas

- AI Context 注入（Phase 5）
- PreToolUse hook 自动触发（Phase 6）
- 24h Blocking 机制（Phase 7）
