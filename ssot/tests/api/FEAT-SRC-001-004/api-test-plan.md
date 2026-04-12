# API Test Plan — FEAT-SRC-001-004

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-001-004 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-001-004__mainline-io-and-path-governance.md`
- Acceptance Checks: 3 条 (AC-01 主链 IO 边界必须明确, AC-02 路径治理不得扩张为全局文件治理, AC-03 正式写入不得回退为自由写入)

## Capabilities Extracted from FEAT

从 FEAT-SRC-001-004 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| io_scope | validate_mainline_io, detect_out_of_scope_io |
| path_governance | enforce_path_boundary, block_scope_expansion |
| write_enforcement | enforce_write_mode, prevent_silent_fallback |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | IO-SCOPE-001 | 主链 IO 边界验证 | 验证哪些 IO 属于 mainline handoff/materialization，哪些明确超出作用域 | P0 |
| 2 | PATH-GOVERNANCE-001 | 路径治理边界 | 阻止路径治理扩张为全局文件治理，维持受治理 scope | P0 |
| 3 | WRITE-ENFORCEMENT-001 | 写入模式强制 | 确保正式写入遵守 path/mode 边界，不得 silent fallback 到自由写入 | P0 |
| 4 | PATH-INHERITANCE-001 | 路径规则继承 | 验证下游 skill 继承路径与目录治理的统一约束 | P1 |

## Test Dimension Matrix

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
| IO-SCOPE-001 | 边界值 | IO 边界为离散分类判定 | ADR-047 Section 4.1.3 |
| PATH-GOVERNANCE-001 | 边界值 | 路径治理边界为离散规则 | ADR-047 Section 4.1.3 |
| WRITE-ENFORCEMENT-001 | 边界值 | 写入模式为离散枚举 | ADR-047 Section 4.1.3 |
| PATH-INHERITANCE-001 | 状态约束 | P1 能力，状态约束裁剪 | ADR-047 Section 4.1.3 |
| PATH-INHERITANCE-001 | 权限与身份 | 试点阶段无鉴权层 | ADR-047 Section 4.1.3 |
| PATH-INHERITANCE-001 | 幂等/重试/并发 | P1 能力，并发场景裁剪 | ADR-047 Section 4.1.3 |
| PATH-INHERITANCE-001 | 边界值 | 继承验证为离散规则检查 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | IO-SCOPE-001, PATH-GOVERNANCE-001, WRITE-ENFORCEMENT-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | PATH-INHERITANCE-001 | 正常路径, 参数校验 (key), 异常路径 (key) |
