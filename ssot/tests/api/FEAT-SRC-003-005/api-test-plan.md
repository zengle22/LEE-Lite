# API Test Plan — FEAT-SRC-003-005

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-003-005 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-003-005__下游-skill-自动派发流.md`
- Acceptance Checks: 3 条 (Claimed job invokes next skill, Dispatch preserves lineage, Holdable approvals not auto-dispatched)

## Capabilities Extracted from FEAT

从 FEAT-SRC-003-005 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| skill_dispatch | invoke_next_skill, preserve_input_refs |
| progression_gate | check_auto_continue, block_hold |
| invocation_record | record_authoritative_invocation, track_lineage |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | DISPATCH-INV-001 | 调用下游 Skill | 将 claimed job 以 authoritative input package 派发到声明的 next skill | P0 |
| 2 | DISPATCH-LINEAGE-001 | 派发溯源 | 派发过程保留上游 refs、job refs 和 target-skill lineage | P0 |
| 3 | PROG-CHECK-001 | Progression Mode 检查 | 仅 `auto-continue` 的 approve 才被自动派发，hold 的不得被自动派发 | P0 |
| 4 | DISPATCH-FAIL-001 | 派发失败回写 | 执行启动失败时回写 execution outcome 而非静默丢失 | P0 |
| 5 | INPUT-VALIDATE-001 | 输入包校验 | 校验 authoritative input refs 的完整性和可达性 | P0 |

## Test Dimension Matrix

每个 capability 按以下维度评估覆盖范围：

| 维度 | 说明 |
|------|------|
| **正常路径** | 合法输入、正确响应、正确副作用 |
| **参数校验** | 必填缺失、类型错误、格式错误、非法枚举、越界值 |
| **边界值** | 最小值/最大值、空集合/空字符串 |
| **状态约束** | 合法状态迁移、非法状态迁移、重复提交 |
| **权限与身份** | 未授权访问、无权限操作 |
| **异常路径** | 资源不存在、冲突、上游依赖失败、业务拒绝 |
| **幂等/重试/并发** | 重复请求、并发提交 |
| **数据副作用** | DB 正确写入、关联对象同步变化 |

## Coverage Cut Records

| Capability | Dimension | Cut Reason | Source Ref |
|------------|-----------|------------|------------|
| DISPATCH-LINEAGE-001 | 边界值 | Lineage 为元数据关联，无连续边界 | ADR-047 Section 4.1.3 |
| INPUT-VALIDATE-001 | 幂等/重试/并发 | 纯校验操作，无并发副作用 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | DISPATCH-INV-001, DISPATCH-LINEAGE-001, PROG-CHECK-001, DISPATCH-FAIL-001, INPUT-VALIDATE-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
